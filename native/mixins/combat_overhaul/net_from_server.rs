fn combat_net_from_server(channel: &str, data: &[u8]) {
    use crate::game::lan_actions::combat_overhaul as m;
    m::from_server(channel, data);
}
