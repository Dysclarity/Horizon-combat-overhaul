// Appended to the combat module by the bundle generator. Server-approved
// swings drive player arms, which carry vanilla held-item geometry with them.
const POSE_CHANNEL: &str = "combat_overhaul:pose";

#[derive(Clone, Copy, Debug, PartialEq)]
struct RemoteSwing {
    started: Instant,
    weapon: usize,
    duration: f32,
}

#[derive(Default)]
struct RemoteAnimations {
    session: Option<u64>,
    players: HashMap<u128, [Option<RemoteSwing>; 2]>,
}

thread_local! {
    static REMOTE_ANIMATIONS: RefCell<RemoteAnimations> = RefCell::new(RemoteAnimations::default());
}

#[derive(Debug)]
struct CombatBodyPose {
    previous: Option<std::sync::Arc<dyn horizon_client::mobs::anim::BodyPose>>,
    swings: [Option<RemoteSwing>; 2],
    left_main: bool,
}

impl horizon_client::mobs::anim::BodyPose for CombatBodyPose {
    fn pose(&self, age: f32, at_rest: &[[f32; 9]; 6], poses: &mut [[f32; 9]; 6]) -> bool {
        let mut changed = self
            .previous
            .as_ref()
            .is_some_and(|prior| prior.pose(age, at_rest, poses));
        for (hand, swing) in self.swings.iter().enumerate() {
            let Some(swing) = swing else {
                continue;
            };
            let progress = swing.started.elapsed().as_secs_f32() / swing.duration;
            if progress >= 1.0 {
                continue;
            }
            let left = (hand == 0) == self.left_main;
            let arm = if left { 3 } else { 2 };
            let delta = pose(WEAPONS[swing.weapon].frames, progress, left);
            // Model coordinates use pixels, downward Y, and radians.
            // Raise the arm during the swing so thrusts project forward.
            let lift = (std::f32::consts::PI * progress).sin();
            poses[arm][0] += delta[3] * 16.0;
            poses[arm][1] -= delta[4] * 16.0;
            poses[arm][2] += delta[5] * 16.0;
            poses[arm][3] += delta[0].to_radians() - 0.8 * lift;
            poses[arm][4] += delta[1].to_radians();
            poses[arm][5] += delta[2].to_radians();
            changed = true;
        }
        changed
    }
}

fn combat_body_pose(mob: &horizon_client::mobs::Mob) -> Option<&CombatBodyPose> {
    let any: &dyn std::any::Any = &**mob.emote.as_ref()?;
    any.downcast_ref::<CombatBodyPose>()
}

fn update_body_pose(mob: &mut horizon_client::mobs::Mob, swings: [Option<RemoteSwing>; 2]) {
    let left_main = mob.main_arm_left();
    if let Some(current) = combat_body_pose(mob) {
        if current.swings == swings && current.left_main == left_main {
            return;
        }
    }
    // Unwrap only our own overlay. Another mod's replacement remains its base.
    let previous = combat_body_pose(mob)
        .map(|p| p.previous.clone())
        .unwrap_or_else(|| mob.emote.clone());
    mob.emote = if swings.iter().any(Option::is_some) {
        Some(std::sync::Arc::new(CombatBodyPose {
            previous,
            swings,
            left_main,
        }))
    } else {
        previous
    };
}

pub fn remote_frame(game: &mut Game<'_>) {
    if !game.native_window() {
        return;
    }
    let enabled = game.native_on(ID);
    let session = game.remote.as_ref().map(|remote| remote.session.serial());
    REMOTE_ANIMATIONS.with(|animations| {
        let mut animations = animations.borrow_mut();
        if animations.session != session || !enabled || game.native_player().is_none() {
            animations.players.clear();
            animations.session = session;
        }
        animations.players.retain(|_, swings| {
            for swing in swings.iter_mut() {
                if swing.is_some_and(|s| s.started.elapsed().as_secs_f32() >= s.duration) {
                    *swing = None;
                }
            }
            swings.iter().any(Option::is_some)
        });
        let own = game.remote.as_ref().map(|remote| remote.profile());
        if let Some(mob) = game.player_model.as_mut() {
            let swings = own
                .and_then(|uuid| animations.players.get(&uuid))
                .copied()
                .unwrap_or_default();
            update_body_pose(mob, swings);
        }
        for mob in game
            .mobs
            .iter_mut()
            .filter(|mob| &*mob.kind.id == "minecraft:player")
        {
            let uuid = game
                .remote
                .as_ref()
                .and_then(|remote| remote.player_uuid(mob.id));
            let swings = uuid
                .and_then(|uuid| animations.players.get(&uuid))
                .copied()
                .unwrap_or_default();
            update_body_pose(mob, swings);
        }
    });
}

pub fn remote_receive(game: &mut Game<'_>, player: u128, hand: usize, item: &str, duration: f32) {
    let Some(weapon) = weapon(item) else {
        return;
    };
    let Some(index) = WEAPONS
        .iter()
        .position(|candidate| candidate.id == weapon.id)
    else {
        return;
    };
    if hand > 1 || !duration.is_finite() || !(0.05..=3.0).contains(&duration) {
        return;
    }
    let mut packet = Vec::with_capacity(23);
    packet.push(1);
    packet.extend_from_slice(&player.to_be_bytes());
    packet.push(hand as u8);
    packet.push(index as u8);
    packet.extend_from_slice(&duration.to_be_bytes());
    for observer in game.native_server_players() {
        let _ = game.native_net_send_to_player(observer.uuid, POSE_CHANNEL, &packet);
    }
}

pub fn remote_packet(channel: &str, data: &[u8]) {
    if channel != POSE_CHANNEL || data.len() != 23 || data[0] != 1 || data[17] > 1 {
        return;
    }
    let index = usize::from(data[18]);
    if index >= WEAPONS.len() {
        return;
    }
    let Ok(uuid) = <[u8; 16]>::try_from(&data[1..17]) else {
        return;
    };
    let Ok(duration) = <[u8; 4]>::try_from(&data[19..23]) else {
        return;
    };
    let duration = f32::from_be_bytes(duration);
    if !duration.is_finite() || !(0.05..=3.0).contains(&duration) {
        return;
    }
    let player = u128::from_be_bytes(uuid);
    REMOTE_ANIMATIONS.with(|animations| {
        let mut animations = animations.borrow_mut();
        if animations.players.len() >= 1024 && !animations.players.contains_key(&player) {
            return;
        }
        animations.players.entry(player).or_default()[usize::from(data[17])] = Some(RemoteSwing {
            started: Instant::now(),
            weapon: index,
            duration,
        });
    });
}
