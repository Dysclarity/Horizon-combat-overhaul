fn combat_net_from_client(
    game: &mut crate::game::Game<'_>,
    player: u128,
    channel: &str,
    data: &[u8],
) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::receive(game, player, channel, data);
}
