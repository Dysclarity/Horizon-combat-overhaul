fn combat_attack_entity(game: &crate::game::Game<'_>, canceled: &mut bool) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::guard(game, canceled);
}
