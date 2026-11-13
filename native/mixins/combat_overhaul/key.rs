fn combat_key(game: &mut crate::game::Game<'_>, key: &str, pressed: bool) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::key(game, key, pressed);
}
