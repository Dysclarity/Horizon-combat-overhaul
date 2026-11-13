"""Embed the shared catalog and testable combat math in Horizon's mixin module."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
native = root / "native"
bundle = native / "mixins/combat_overhaul"
data = json.loads((root / "design/weapons.json").read_text())
core = (native / "core.rs").read_text().split("#[cfg(test)]")[0]
rows = []
for w in data["weapons"]:
    frames = ",".join("[" + ",".join(str(float(v)) for v in row) + "]" for row in w["animation"]["keyframes"])
    rows.append(f'Weapon {{ id: "{w["id"]}", offhand: {str(w["offhand"]).lower()}, speed: {float(w["attack_speed"])}, reach: {float(w["reach"])}, frames: &[{frames}] }}')
(bundle / "runtime.rs").write_text(core + "\nstatic WEAPONS: &[Weapon] = &[\n" + ",\n".join(rows) + "\n];\n" + (native / "runtime_body.rs").read_text() + "\n" + (native / "remote_animation_body.rs").read_text())
pin = "36eb98b6f6ec4f22649cbe65bbfd32bc0dc2083f"
manifest = f'''[mod]
id = "combat_overhaul"
version = "0.1.1"
priority = 100
[compatibility]
horizon_revision = "{pin}"
[[module]]
id = "runtime"
file = "crates/horizon-client/src/game/lan_actions.rs"
name = "combat_overhaul"
source = "runtime.rs"
'''
game = ("game", "&mut crate::game::Game<'_>", "&mut *self")
readonly = ("game", "&crate::game::Game<'_>", "&*self")
hooks = [
    ("server_stopped", [], "m::reset_server();"),
    ("living_incoming_damage", [("damage_type", "&str", "damage_type"), ("amount", "&mut f32", "&mut *amount")], "m::damage(damage_type, amount);"),
    ("frame", [game, ("elapsed", "std::time::Duration", "elapsed")], "m::frame(game, elapsed);"),
    ("key", [game, ("key", "&str", "key"), ("pressed", "bool", "pressed")], "m::key(game, key, pressed);"),
    ("tick", [game], "m::tick(game);"),
    ("net_from_client", [game, ("player", "u128", "player"), ("channel", "&str", "channel"), ("data", "&[u8]", "data")], "m::receive(game, player, channel, data);"),
    ("net_from_server", [("channel", "&str", "channel"), ("data", "&[u8]", "data")], "m::from_server(channel, data);"),
    ("interaction_key", [readonly, ("button", "i32", "button"), ("swing", "&mut bool", "&mut *swing_hand"), ("canceled", "&mut bool", "&mut *canceled")], "m::interaction(game, button, swing, canceled);"),
    ("attack_entity", [readonly, ("canceled", "&mut bool", "&mut *canceled")], "m::guard(game, canceled);"),
    ("render_hand_pose", [readonly, ("hand", "horizon_client::first_person::Hand", "hand"), ("stack", "Option<&horizon_client::items::ItemStack>", "stack")] + [(k, "&mut f32", "&mut *"+k) for k in ["pitch","yaw","roll","x","y","z"]], "m::render(game, hand, stack, [pitch, yaw, roll, x, y, z]);"),
    ("mods", [("mods", "&mut Vec<crate::game::native_hooks::NativeMod>", "&mut *mods")], '''mods.push(crate::game::native_hooks::NativeMod { id: "combat_overhaul".into(), title: "Combat Overhaul 0.1.1".into(), description: "Deliberate combat and independent weapon hands. Requires Combat Overhaul on the server.".into(), keys: vec![["main_attack".into(), "Main-hand attack".into(), "key.mouse.left".into()], ["off_attack".into(), "Off-hand attack".into(), "key.mouse.right".into()]] });'''),
]
for name, bindings, body in hooks:
    args = ", ".join(f"{n}: {t}" for n,t,v in bindings)
    prefix = "use crate::game::lan_actions::combat_overhaul as m;" if name != "mods" else ""
    (bundle / f"{name}.rs").write_text(f"fn combat_{name}({args}) {{\n    {prefix}\n    {body}\n}}\n")
    manifest += f'''\n[[injection]]
id = "{name}"
kind = "HEAD"
target = "horizon_client::game::native_hooks::Game<'_>::native_{name}"
helper = "{name}.rs"
bindings = [
'''
    manifest += "\n".join("  { name = " + json.dumps(n) + ", ty = " + json.dumps(t) + ", value = " + json.dumps(v) + " }," for n,t,v in bindings)
    manifest += "\n]\n"
(bundle / "horizon-mixin.toml").write_text(manifest)
(native / "compatibility.json").write_text(json.dumps({"game":"26.3", "horizon_repository":"https://github.com/horizon-rust/horizon", "horizon_revision":pin, "horizon_mixins_repository":"https://github.com/horizon-rust/horizon-mixins", "horizon_mixins_revision":"5a64af938ec86b00d53d16a408aabc0038fb3e57"}, indent=2)+"\n")

subprocess.run(["rustfmt", "--edition", "2024", *map(str, sorted(bundle.glob("*.rs")))], check=True)
