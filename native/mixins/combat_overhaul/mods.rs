fn combat_mods(mods: &mut Vec<crate::game::native_hooks::NativeMod>) {
    mods.push(crate::game::native_hooks::NativeMod { id: "combat_overhaul".into(), title: "Combat Overhaul 0.1.1".into(), description: "Deliberate combat and independent weapon hands. Requires Combat Overhaul on the server.".into(), keys: vec![["main_attack".into(), "Main-hand attack".into(), "key.mouse.left".into()], ["off_attack".into(), "Off-hand attack".into(), "key.mouse.right".into()]] });
}
