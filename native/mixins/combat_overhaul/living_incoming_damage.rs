fn combat_living_incoming_damage(damage_type: &str, amount: &mut f32) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::damage(damage_type, amount);
}
