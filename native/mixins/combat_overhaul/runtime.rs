#[derive(Clone, Copy, Debug)]
pub struct Weapon {
    pub id: &'static str,
    pub offhand: bool,
    pub speed: f32,
    pub reach: f64,
    pub frames: &'static [[f32; 7]],
}

pub fn ray_box(
    eye: [f64; 3],
    dir: [f64; 3],
    lo: [f64; 3],
    hi: [f64; 3],
    reach: f64,
) -> Option<f64> {
    let mut near: f64 = 0.0;
    let mut far = reach;
    for a in 0..3 {
        if dir[a].abs() < 1e-9 {
            if eye[a] < lo[a] || eye[a] > hi[a] {
                return None;
            }
        } else {
            let x = (lo[a] - eye[a]) / dir[a];
            let y = (hi[a] - eye[a]) / dir[a];
            near = near.max(x.min(y));
            far = far.min(x.max(y));
        }
    }
    (near <= far && far >= 0.0).then_some(near)
}

pub fn pose(frames: &[[f32; 7]], progress: f32, offhand: bool) -> [f32; 6] {
    let mut result = [0.0; 6];
    if !progress.is_finite() || !(0.0..1.0).contains(&progress) {
        return result;
    }
    for pair in frames.windows(2) {
        if progress >= pair[0][0] && progress <= pair[1][0] {
            let t = (progress - pair[0][0]) / (pair[1][0] - pair[0][0]);
            let t = t * t * (3.0 - 2.0 * t);
            for i in 0..6 {
                result[i] = pair[0][i + 1] + (pair[1][i + 1] - pair[0][i + 1]) * t;
            }
            break;
        }
    }
    if offhand {
        result[1] = -result[1];
        result[2] = -result[2];
        result[3] = -result[3];
    }
    result
}

pub fn request(data: &[u8]) -> Option<usize> {
    match data {
        [1, hand @ 0..=1] => Some(*hand as usize),
        _ => None,
    }
}

static WEAPONS: &[Weapon] = &[
    Weapon {
        id: "dagger",
        offhand: true,
        speed: 2.5,
        reach: 2.3,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.18, 12.0, -8.0, -8.0, 0.0, -0.04, 0.1],
            [0.35, -12.0, 5.0, -5.0, 0.0, 0.02, -0.42],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "short_sword",
        offhand: true,
        speed: 2.0,
        reach: 2.6,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.22, 8.0, -24.0, -32.0, 0.1, 0.04, 0.04],
            [0.42, -14.0, 27.0, 42.0, -0.2, -0.06, -0.16],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "arming_sword",
        offhand: false,
        speed: 1.4,
        reach: 3.0,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.25, 18.0, -32.0, -48.0, 0.12, 0.1, 0.08],
            [0.46, -26.0, 35.0, 56.0, -0.22, -0.15, -0.23],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "longsword",
        offhand: false,
        speed: 1.1,
        reach: 3.2,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.28, 25.0, -38.0, -56.0, 0.15, 0.13, 0.12],
            [0.49, -34.0, 43.0, 66.0, -0.27, -0.19, -0.27],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "greatsword",
        offhand: false,
        speed: 0.75,
        reach: 3.4,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.36, 48.0, -28.0, -65.0, 0.17, 0.22, 0.2],
            [0.58, -58.0, 34.0, 78.0, -0.3, -0.3, -0.33],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "rapier",
        offhand: true,
        speed: 2.1,
        reach: 3.2,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.24, 5.0, -5.0, -14.0, 0.04, -0.02, 0.15],
            [0.4, -8.0, 2.0, -14.0, 0.01, 0.02, -0.65],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "estoc",
        offhand: false,
        speed: 1.2,
        reach: 3.5,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.3, 10.0, -7.0, -20.0, 0.06, -0.06, 0.23],
            [0.48, -13.0, 3.0, -20.0, 0.02, 0.03, -0.74],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "cutlass",
        offhand: true,
        speed: 1.6,
        reach: 2.6,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.23, 0.0, -42.0, -18.0, 0.15, 0.04, 0.08],
            [0.44, -7.0, 48.0, 34.0, -0.26, -0.02, -0.18],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "saber",
        offhand: false,
        speed: 1.6,
        reach: 3.0,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.22, 12.0, -36.0, -35.0, 0.17, 0.08, 0.12],
            [0.43, -20.0, 54.0, 49.0, -0.3, -0.1, -0.1],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "scimitar",
        offhand: false,
        speed: 1.3,
        reach: 3.0,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.27, 17.0, -48.0, -31.0, 0.21, 0.07, 0.1],
            [0.48, -24.0, 62.0, 57.0, -0.34, -0.12, -0.19],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "katana",
        offhand: false,
        speed: 1.2,
        reach: 3.1,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.28, 38.0, -18.0, -40.0, 0.1, 0.21, 0.12],
            [0.44, -42.0, 24.0, 52.0, -0.19, -0.24, -0.31],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "spear",
        offhand: false,
        speed: 1.05,
        reach: 3.8,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.29, 16.0, -4.0, -28.0, 0.06, -0.06, 0.22],
            [0.47, -9.0, 2.0, -28.0, 0.01, 0.01, -0.84],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "pike",
        offhand: false,
        speed: 0.8,
        reach: 4.3,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.35, 18.0, -2.0, -32.0, 0.03, -0.09, 0.29],
            [0.53, -6.0, 1.0, -32.0, 0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "halberd",
        offhand: false,
        speed: 0.85,
        reach: 3.8,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.34, 52.0, -20.0, -28.0, 0.16, 0.27, 0.2],
            [0.56, -61.0, 26.0, 47.0, -0.25, -0.32, -0.4],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "glaive",
        offhand: false,
        speed: 1.0,
        reach: 3.7,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.31, 20.0, -56.0, -25.0, 0.24, 0.12, 0.19],
            [0.52, -28.0, 70.0, 44.0, -0.38, -0.14, -0.33],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "battleaxe",
        offhand: false,
        speed: 0.7,
        reach: 3.0,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.37, 64.0, -16.0, -22.0, 0.11, 0.28, 0.21],
            [0.59, -72.0, 21.0, 36.0, -0.17, -0.36, -0.28],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "warhammer",
        offhand: false,
        speed: 0.6,
        reach: 2.9,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.4, 78.0, -8.0, -12.0, 0.07, 0.33, 0.24],
            [0.62, -85.0, 12.0, 20.0, -0.1, -0.42, -0.32],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "mace",
        offhand: false,
        speed: 0.95,
        reach: 2.7,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.32, 46.0, -26.0, -20.0, 0.13, 0.19, 0.17],
            [0.54, -54.0, 32.0, 38.0, -0.21, -0.26, -0.22],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "club",
        offhand: true,
        speed: 1.4,
        reach: 2.4,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.26, 35.0, -18.0, -15.0, 0.1, 0.12, 0.1],
            [0.47, -40.0, 24.0, 29.0, -0.16, -0.17, -0.16],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
    Weapon {
        id: "sickle",
        offhand: true,
        speed: 2.0,
        reach: 2.4,
        frames: &[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.23, -12.0, 31.0, 26.0, -0.12, 0.06, -0.05],
            [0.44, 18.0, -43.0, -48.0, 0.23, -0.09, 0.16],
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    },
];
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
