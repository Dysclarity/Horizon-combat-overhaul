fn combat_interaction_key(
    game: &crate::game::Game<'_>,
    button: i32,
    swing: &mut bool,
    canceled: &mut bool,
) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::interaction(game, button, swing, canceled);
}
