fn combat_render_hand_pose(
    game: &crate::game::Game<'_>,
    hand: horizon_client::first_person::Hand,
    stack: Option<&horizon_client::items::ItemStack>,
    pitch: &mut f32,
    yaw: &mut f32,
    roll: &mut f32,
    x: &mut f32,
    y: &mut f32,
    z: &mut f32,
) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::render(game, hand, stack, [pitch, yaw, roll, x, y, z]);
}
