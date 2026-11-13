fn combat_frame(game: &mut crate::game::Game<'_>, elapsed: std::time::Duration) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::frame(game, elapsed);
}
