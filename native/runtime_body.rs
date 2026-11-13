use crate::game::Game;
use horizon_client::{first_person::Hand, items::ItemStack};
use std::{
    cell::RefCell,
    collections::HashMap,
    time::{Duration, Instant},
};

const ID: &str = "combat_overhaul";
const ATTACK: &str = "combat_overhaul:attack";
const RESULT: &str = "combat_overhaul:result";
const HELLO: &str = "combat_overhaul:hello";
#[derive(Clone)]
struct Pending {
    hand: usize,
    item: String,
    snapshot: ItemStack,
    selected: usize,
    conn: u32,
    dimension: String,
    impact: i64,
}
#[derive(Default)]
struct Fighter {
    ready: [i64; 2],
    global: i64,
    pending: Vec<Pending>,
    seen: i64,
}
#[derive(Default)]
struct Client {
    active: [Option<(Instant, String)>; 2],
    hello: Option<Instant>,
    server: Option<Instant>,
    last: [Option<Instant>; 2],
    pressed: std::collections::HashSet<String>,
}
thread_local! {
    static CLIENT: RefCell<Client> = RefCell::new(Client::default());
    static FIGHTERS: RefCell<HashMap<u128, Fighter>> = RefCell::new(HashMap::new());
    static OFFHAND: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
    static EXECUTING: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

fn weapon(item: &str) -> Option<&'static Weapon> {
    let name = item.strip_prefix("combat_overhaul:")?;
    let (material, kind) = name.split_once('_')?;
    if ![
        "wood",
        "stone",
        "iron",
        "gold",
        "copper",
        "diamond",
        "netherite",
    ]
    .contains(&material)
    {
        return None;
    }
    WEAPONS.iter().find(|w| w.id == kind)
}
fn stack<'a>(game: &'a Game<'_>, hand: usize) -> Option<&'a ItemStack> {
    if hand == 0 {
        game.inventory.get(game.selected)?.as_ref()
    } else {
        game.offhand.as_ref()
    }
}
fn usable(game: &Game<'_>, hand: usize) -> Option<&'static Weapon> {
    let w = weapon(&stack(game, hand)?.item)?;
    (hand == 0 || w.offhand).then_some(w)
}
pub fn frame(game: &mut Game<'_>, _elapsed: Duration) {
    remote_frame(game);
    if !game.native_window() {
        return;
    }
    if game.native_player().is_none() || !game.native_on(ID) {
        CLIENT.with(|c| *c.borrow_mut() = Client::default());
        return;
    }
    if !game.native_playing() {
        CLIENT.with(|c| c.borrow_mut().pressed.clear());
    }
    let now = Instant::now();
    let hello = CLIENT.with(|c| {
        let mut c = c.borrow_mut();
        if c.hello.is_none_or(|t| now.duration_since(t).as_secs() >= 3) {
            c.hello = Some(now);
            true
        } else {
            false
        }
    });
    if hello {
        let _ = game.native_net_send_to_server(HELLO, &[1]);
    }
}
pub fn from_server(channel: &str, data: &[u8]) {
    remote_packet(channel, data);
    if channel == RESULT
        && let [1, hand @ 0..=1, 0] = data
    {
        CLIENT.with(|c| {
            let mut c = c.borrow_mut();
            c.last[*hand as usize] = None;
            c.active[*hand as usize] = None;
        });
    }
    if channel == HELLO && data == [1] {
        CLIENT.with(|c| c.borrow_mut().server = Some(Instant::now()));
    }
}
pub fn key(game: &mut Game<'_>, key: &str, pressed: bool) {
    let first = CLIENT.with(|c| {
        let mut c = c.borrow_mut();
        if pressed {
            c.pressed.insert(key.into())
        } else {
            c.pressed.remove(key);
            false
        }
    });
    if !first || !game.native_on(ID) || !game.native_playing() {
        return;
    }
    let main = game.native_mod_key(ID, "main_attack", "key.mouse.left");
    let off = game.native_mod_key(ID, "off_attack", "key.mouse.right");
    let hand = if key == main {
        0
    } else if key == off {
        1
    } else {
        return;
    };
    let Some(w) = usable(game, hand) else {
        return;
    };
    let now = Instant::now();
    let allowed = CLIENT.with(|c| {
        let c = c.borrow();
        c.server
            .is_some_and(|t| now.duration_since(t).as_secs() < 10)
            && c.last[hand].is_none_or(|t| {
                now.duration_since(t).as_secs_f32() >= (20.0 / w.speed).ceil() / 20.0
            })
            && c.last
                .iter()
                .all(|t| t.is_none_or(|t| now.duration_since(t).as_secs_f32() >= 0.2))
    });
    if !allowed {
        return;
    }
    let item = stack(game, hand).unwrap().item.to_string();
    if game
        .native_net_send_to_server(ATTACK, &[1, hand as u8])
        .is_ok()
    {
        CLIENT.with(|c| {
            let mut c = c.borrow_mut();
            c.last[hand] = Some(now);
            c.active[hand] = Some((now, item));
        });
    }
}
pub fn interaction(game: &Game<'_>, button: i32, swing: &mut bool, canceled: &mut bool) {
    if game.native_on(ID)
        && ((button == 0 && usable(game, 0).is_some())
            || (button == 1 && usable(game, 1).is_some()))
    {
        *canceled = true;
        *swing = false;
    }
}
pub fn guard(game: &Game<'_>, canceled: &mut bool) {
    if game.native_on(ID) && usable(game, 0).is_some() && !EXECUTING.with(|v| v.get()) {
        *canceled = true;
    }
}
pub fn receive(game: &mut Game<'_>, player: u128, channel: &str, data: &[u8]) {
    if !game.native_on(ID) {
        return;
    }
    if channel == HELLO && data == [1] {
        let _ = game.native_net_send_to_player(player, HELLO, &[1]);
        return;
    }
    if channel != ATTACK {
        return;
    }
    let Some(hand) = request(data) else {
        return;
    };
    let Some(host) = game.lan.as_ref() else {
        return;
    };
    let Some(g) = host.hub.guests.iter().find(|g| {
        g.uuid == player
            && g.placed
            && g.client_loaded()
            && g.health > 0.0
            && host.hub.here(g)
            && !g.spectator()
    }) else {
        return;
    };
    let item = if hand == 0 {
        g.inventory.get(g.selected).and_then(|s| s.as_ref())
    } else {
        g.offhand.as_ref()
    };
    let Some(item) = item.filter(|s| s.count > 0) else {
        return;
    };
    let Some(w) = weapon(&item.item).filter(|w| hand == 0 || w.offhand) else {
        return;
    };
    let item_name = item.item.to_string();
    let tick = game.world.game_time;
    let mut accepted = false;
    FIGHTERS.with(|fighters| {
        let mut fighters = fighters.borrow_mut();
        let f = fighters.entry(player).or_default();
        if tick < f.seen {
            *f = Fighter::default();
        }
        f.seen = tick;
        if tick < f.ready[hand] || tick < f.global {
            return;
        }
        let cooldown = (20.0 / w.speed).ceil() as i64;
        f.ready[hand] = tick + cooldown;
        f.global = tick + 4;
        let impact = (cooldown as f32 * w.frames[2][0]).round().max(1.0) as i64;
        f.pending.push(Pending {
            hand,
            item: item.item.to_string(),
            snapshot: item.clone(),
            selected: g.selected,
            conn: g.conn,
            dimension: g.dimension.clone(),
            impact: tick + impact,
        });
        accepted = true;
    });
    let _ = game.native_net_send_to_player(player, RESULT, &[1, hand as u8, u8::from(accepted)]);
    if accepted {
        remote_receive(
            game,
            player,
            hand,
            &item_name,
            (20.0 / w.speed).ceil() / 20.0,
        );
    }
}
pub fn tick(game: &mut Game<'_>) {
    if game.native_window() {
        return;
    }
    if !game.native_on(ID) {
        reset_server();
        return;
    }
    let now = game.world.game_time;
    let due = FIGHTERS.with(|fighters| {
        let mut fighters = fighters.borrow_mut();
        let mut due = Vec::new();
        fighters.retain(|_, f| now >= f.seen && now - f.seen < 600);
        for (&player, f) in fighters.iter_mut() {
            f.pending.retain(|p| {
                if p.impact <= now && p.dimension == game.dim.id() {
                    due.push((player, p.clone()));
                    false
                } else {
                    true
                }
            });
        }
        due
    });
    for (player, pending) in due {
        strike(game, player, pending);
    }
}
fn strike(game: &mut Game<'_>, player: u128, pending: Pending) {
    let Some(mut host) = game.lan.take() else {
        return;
    };
    let Some(gi) = host.hub.guests.iter().position(|g| {
        g.uuid == player
            && g.placed
            && g.client_loaded()
            && g.health > 0.0
            && host.hub.here(g)
            && !g.spectator()
    }) else {
        game.lan = Some(host);
        return;
    };
    if host.hub.guests[gi].conn != pending.conn
        || host.hub.guests[gi].selected != pending.selected
        || host.hub.guests[gi].health <= 0.0
    {
        game.lan = Some(host);
        return;
    }
    let conn = host.hub.guests[gi].conn;
    let selected = host.hub.guests[gi].selected;
    let previous_swing = host.play.get(&conn).map(|play| (play.swing, play.swings));
    let item = if pending.hand == 0 {
        host.hub.guests[gi]
            .inventory
            .get(selected)
            .and_then(|s| s.as_ref())
    } else {
        host.hub.guests[gi].offhand.as_ref()
    };
    if item.is_none_or(|s| s.count == 0 || s != &pending.snapshot) {
        game.lan = Some(host);
        return;
    }
    let Some(w) = weapon(&pending.item) else {
        game.lan = Some(host);
        return;
    };
    // Move the actual stack, including its components and damage, through the normal melee path.
    if pending.hand == 1 {
        let g = &mut host.hub.guests[gi];
        std::mem::swap(&mut g.inventory[selected], &mut g.offhand);
    }
    let boxes: Vec<_> = host
        .hub
        .guests
        .iter()
        .filter(|g| g.conn != conn && host.hub.here(g) && !g.spectator())
        .map(|g| (g.entity_id, g.bounds()))
        .chain(
            game.mobs
                .iter()
                .filter(|m| m.alive())
                .map(|m| (m.id as i32, m.bounds())),
        )
        .collect();
    let target = game
        .as_guest(&mut host, conn, |g| {
            let (eye, dir) = g.aim()?;
            boxes
                .iter()
                .filter_map(|(id, bounds)| {
                    let lo = bounds.min_position();
                    let hi = bounds.max_position();
                    let distance =
                        ray_box(eye, dir, [lo.x, lo.y, lo.z], [hi.x, hi.y, hi.z], w.reach)?;
                    g.before_block(distance).then_some((*id, distance))
                })
                .min_by(|a, b| a.1.total_cmp(&b.1))
                .map(|v| v.0)
        })
        .flatten();
    EXECUTING.with(|v| v.set(true));
    OFFHAND.with(|v| v.set(pending.hand == 1));
    if let Some(target) = target {
        // Independent hand cooldowns provide full attack strength at impact.
        game.as_guest(&mut host, conn, |g| {
            g.attack_ticks = 100;
            g.apply_equipment();
        });
        game.guest_attack(&mut host, conn, target);
    }
    EXECUTING.with(|v| v.set(false));
    OFFHAND.with(|v| v.set(false));
    if pending.hand == 1 {
        let g = &mut host.hub.guests[gi];
        std::mem::swap(&mut g.inventory[selected], &mut g.offhand);
    }
    game.as_guest(&mut host, conn, |g| g.apply_equipment());
    // Vanilla stores one swing for both hands. Our accepted attacks already
    // animate each hand independently, so keep melee's incidental swing out
    // of the tick-end broadcast and preserve any unrelated vanilla animation.
    if let Some((swing, swings)) = previous_swing
        && let Some(play) = host.play.get_mut(&conn)
    {
        play.swing = swing;
        play.swings = swings;
    }
    host.hub.send_inventory(gi);
    game.lan = Some(host);
}
pub fn damage(damage_type: &str, amount: &mut f32) {
    if damage_type == "minecraft:player_attack" && OFFHAND.with(|v| v.get()) {
        *amount *= 0.85;
    }
}
pub fn render(game: &Game<'_>, hand: Hand, item: Option<&ItemStack>, values: [&mut f32; 6]) {
    if !game.native_on(ID) {
        return;
    }
    let h = if hand == Hand::Main { 0 } else { 1 };
    let Some(item) = item else {
        return;
    };
    let Some(w) = weapon(&item.item) else {
        return;
    };
    let delta = CLIENT.with(|c| {
        let c = c.borrow();
        let Some((start, id)) = &c.active[h] else {
            return [0.0; 6];
        };
        if id != &*item.item {
            return [0.0; 6];
        }
        pose(
            w.frames,
            start.elapsed().as_secs_f32() / ((20.0 / w.speed).ceil() / 20.0),
            (h == 0) == game.settings.main_hand_left,
        )
    });
    for (v, d) in values.into_iter().zip(delta) {
        *v += d;
    }
}

pub fn reset_server() {
    FIGHTERS.with(|fighters| fighters.borrow_mut().clear());
}
