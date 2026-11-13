# Combat Overhaul for Horizon

140 craftable melee weapons, covering 20 designs in wood, stone, iron, gold, copper, diamond, and netherite. The arsenal uses hand-authored 16×16 textures for compact weapons and 32×32 textures for long blades and polearms, with Minecraft handheld item models. Combat timing varies by weapon, from quick daggers to slow heavy attacks with a windup.

The content and Rust combat code are packaged together in [dist/combat_overhaul-0.1.1.hmod](dist/combat_overhaul-0.1.1.hmod). The separate `-content.hmod` contains the arsenal alone. Install the combined package for the combat overhaul.

## Controls

Left click attacks with the main hand. Right click attacks with an eligible offhand weapon. Daggers, short swords, rapiers, cutlasses, clubs, and sickles can attack from the offhand. Set both attack bindings in **Options → Mods → Combat Overhaul**. Heavy weapons can be paired with an eligible offhand weapon.

Each hand has its own cooldown. The initial balance uses 85% damage for offhand attacks and a shared 0.2-second gap between attacks. Weapon designs share their animation across material tiers, with different motions for all 20 designs.

Craft wood through diamond weapons using material ingredients and sticks. Upgrade each diamond weapon to netherite at a smithing table with a netherite upgrade template and netherite ingot. The creative inventory includes a Combat Overhaul tab. The full roster and balance values are in `design/weapons.json`, with a preview in `design/weapon-preview.png`.

## Build and install

This mod pins Horizon revision `36eb98b6f6ec4f22649cbe65bbfd32bc0dc2083f` and horizon-mixins revision `5a64af938ec86b00d53d16a408aabc0038fb3e57`. Its integration accesses server combat internals, so use this exact source revision. Existing older Horizon installations need a native build at the pinned revision.

The Windows developer workflow requires Git, Rust with the MSVC build tools, and Python 3.11 or later. Regenerating textures also requires Pillow.

```powershell
python -m pip install -r requirements-dev.txt
python tools/generate_content.py
python tools/validate_content.py
./tools/build_native.ps1
python tools/package.py
```

`build_native.ps1 -Build` also builds the modded executable. Source checkouts and compilation output stay under `native/`. The mod's generated mixin bundle is `native/mixins/combat_overhaul`.

The launcher accepts the combined `.hmod` as a native mod and compiles it for the selected instance. Enable the matching content in the game and restart to load its registry entries. A source build can instead load `content/` with `--dev-mod` and your prepared Minecraft resources with `--resources`.

## Multiplayer

Every player and the host need the same combined package and modded Horizon build. Horizon's current source supports matching custom registries over LAN and dedicated servers. The server checks the equipped hand, weapon eligibility, cooldown, target range, and obstruction before passing a hit through Horizon's normal combat handling. The client sends the hand to attack with.

For a dedicated server, Horizon's launcher can export the native engine using `native-build <bundle> --server-output <new-directory> --version <installed-base-tag>`, with its native-code trust confirmation. Configure the supervisor's `engine.path` to the exported engine. Keep the matching content enabled on the server and all clients. Source and base-version compatibility must match the pinned revision.

## Validation

`tools/validate_content.py` checks the complete roster, material stats, recipes, smithing upgrades, names, model references, textures, offhand eligibility, and animation timelines. `cargo test --manifest-path native/Cargo.toml` exercises combat math and packet validation. Horizon's official `cargo-horizon-mod` validates both generated packages.

The native runtime source is generated from `native/core.rs`, `native/runtime_body.rs`, `native/remote_animation_body.rs`, and `design/weapons.json` by `native/tools/generate.py`. Edit those inputs before regenerating. The source pin and build script keep engine integration reproducible.

`tools/smoke_multiplayer.py` runs two isolated clients against an integrated LAN server. Supply `--client` with the compiled modded executable, `--ctl` with Horizon's control executable, and `--resources` with prepared Minecraft 26.3 resources. It copies those resources into its test output folder and creates disposable worlds.

A two-player LAN test verified synchronization of all seven material tiers, main-hand damage of 4 health points with a wooden arming sword, offhand damage of 2.55 with a wooden dagger, and zero offhand damage with PvP disabled. Both the host and joining player passed the attack checks. Additional checks passed for offhand durability, preserving the main-hand stack, rapid-click cooldowns, wall obstruction, rebinding both attacks through the UI, and disabling the old binding. The pinned native executable compiled successfully and both packages passed Horizon's official validator. Dedicated-server export has build instructions above, with live multiplayer validation performed over LAN.

## License

MIT, as provided by the repository's existing `LICENSE`.
