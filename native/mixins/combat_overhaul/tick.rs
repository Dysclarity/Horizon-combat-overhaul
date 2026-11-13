fn combat_tick(game: &mut crate::game::Game<'_>) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::tick(game);
}
