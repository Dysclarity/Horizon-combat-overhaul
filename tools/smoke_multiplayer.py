"""Exercise Combat Overhaul through two real headless Horizon clients.

Pass the compiled modded client, horizon-ctl, and prepared 26.3 resources.
Uses upstream's LAN setup and control protocol. A private copy of resources
and disposable game homes keep installed games and saves untouched.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]


def prepare_duel(host, guest):
    for game in (host, guest):
        game("command", command="effect give @s minecraft:instant_health 1 8")
    x, y, z = host("state")["player"]["position"]
    x, z = math.floor(x) + 0.5, math.floor(z) + 0.5
    host("command", command=f"tp @s {x} {y} {z}")
    guest("command", command=f"tp @s {x + 2} {y} {z}")
    guest.wait(25)
    host.raw("look-at", x + 2, y + 1.4, z)
    guest.raw("look-at", x, y + 1.4, z)
    guest.wait(40)
    return x, y, z


def bind_attacks(game, out):
    game.raw("options", "mods")
    widgets = game.raw("ui")["widgets"]
    settings = next(w for w in widgets if w.get("enabled") and w.get("label", "").startswith("Settings"))
    game.raw("click", settings["id"])
    for caption, key in (("Main-hand attack", "r"), ("Off-hand attack", "v")):
        widgets = game.raw("ui")["widgets"]
        label = next(w for w in widgets if w.get("label") == caption)
        button = next(w for w in widgets if w.get("enabled") and abs(w["bounds"][1] - label["bounds"][1]) < 1 and w["bounds"][0] > label["bounds"][0])
        game.raw("click", button["id"])
        game.raw("key", key, "tap")
    game.shot(out, "rebound-settings")
    for _ in range(5):
        if game("state")["screen"] == "playing":
            break
        game.raw("key", "esc", "tap")
    saved = list(game.work.rglob("horizon-mods.txt"))
    assert saved, "native key settings were not saved"
    contents = "\n".join(path.read_text() for path in saved)
    assert "key.keyboard.r" in contents and "key.keyboard.v" in contents, contents


def visual_check(host, guest, out, main="mouse left click", off="mouse right click"):
    from PIL import Image

    x, y, z = prepare_duel(host, guest)
    guest("command", command=f"tp @s {x + 4.5} {y} {z}")
    guest("command", command="item replace entity @s weapon.mainhand with combat_overhaul:iron_greatsword")
    guest("command", command="item replace entity @s weapon.offhand with combat_overhaul:iron_club")
    for game in (host, guest):
        game("options_set", key="chatVisibility", value="2")
        game("options_set", key="tutorialStep", value="none")
    guest.wait(40)
    equipped = guest("status")
    assert (equipped.get("held") or {}).get("item") == "combat_overhaul:iron_greatsword", equipped
    assert (equipped.get("offhand") or {}).get("item") == "combat_overhaul:iron_club", equipped
    host.raw("look-at", x + 4.5, y + 0.9, z)
    guest.raw("look-at", x, y + 1.4, z)
    host.shot(out, "third-person-rest")
    guest.script([main, "wait 4", f'screenshot "{(out / "first-person-swing.png").as_posix()}"'])
    guest.wait(40)
    guest.script([main])
    host.script(["wait 4", f'screenshot "{(out / "third-person-swing.png").as_posix()}"'])
    guest.wait(40)
    guest.script([off])
    host.script(["wait 3", f'screenshot "{(out / "third-person-offhand.png").as_posix()}"'])
    names = ["first-person-swing.png", "third-person-swing.png", "third-person-offhand.png"]
    for name in names:
        with Image.open(out / name) as image:
            image.load()
            assert image.size == (1280, 720), (name, image.size)
    return {"validated_screenshots": names}


def combat_check(host, guest, out):
    results = {}
    host("command", command="gamerule natural_health_regeneration false")
    host("command", command="gamerule pvp true")
    # Keep damage below fatal so each case can restore the same player.
    for game in (host, guest):
        game("command", command="clear @s")
        game("command", command="gamemode survival")
        game("command", command="item replace entity @s weapon.mainhand with combat_overhaul:wood_arming_sword")
        game("command", command="item replace entity @s weapon.offhand with combat_overhaul:wood_dagger")
    # Each material must survive a real server -> client inventory update.
    for material in ("wood", "stone", "iron", "gold", "copper", "diamond", "netherite"):
        guest("command", command=f"give @s combat_overhaul:{material}_spear")
    guest.wait(30)
    inventory = guest("inventory")
    for material in ("wood", "stone", "iron", "gold", "copper", "diamond", "netherite"):
        assert inventory["counts"].get(f"combat_overhaul:{material}_spear", 0) >= 1, inventory
    results["synced_materials"] = 7
    for label, attacker, victim, button, permitted in (
        ("guest_mainhand", guest, host, "left", True),
        ("guest_offhand", guest, host, "right", True),
        ("host_mainhand", host, guest, "left", True),
        ("host_offhand", host, guest, "right", True),
        ("offhand_respects_pvp", guest, host, "right", False),
    ):
        for game in (host, guest):
            game("command", command="effect give @s minecraft:instant_health 1 8")
        host("command", command=f"gamerule pvp {'true' if permitted else 'false'}")
        x, y, z = host("state")["player"]["position"]
        guest("command", command=f"tp @s {x + 1.8} {y} {z}")
        guest.wait(20)
        host.raw("look-at", x + 1.8, y + 1.4, z)
        guest.raw("look-at", x, y + 1.4, z)
        attacker.wait(40)
        before = victim("state")["player"]["health"]
        prior = attacker("status")
        attacker.raw("mouse", button, "click")
        attacker.wait(25)
        after = victim("state")["player"]["health"]
        results[label] = {"before": before, "after": after}
        assert (after < before) if permitted else (after == before), (label, results[label])
        if button == "right" and permitted:
            status = attacker("status")
            assert status["held"] == prior["held"], (label, "mainhand changed", status)
            assert status["offhand"]["item"] == prior["offhand"]["item"], status
            assert status["offhand"]["damage"] > prior["offhand"]["damage"], (label, "offhand durability unchanged", status)
        attacker.shot(out, label)
    host("command", command="gamerule pvp true")
    prepare_duel(host, guest)
    before = host("state")["player"]["health"]
    guest.script(["mouse left click", "mouse left click", "mouse left click", "wait 25"])
    damage = before - host("state")["player"]["health"]
    expected = results["guest_mainhand"]["before"] - results["guest_mainhand"]["after"]
    assert abs(damage - expected) < 0.01, ("cooldown", damage, expected)
    results["cooldown_three_clicks"] = {"damage": damage, "single_attack_damage": expected}

    x, y, z = prepare_duel(host, guest)
    bx, by, bz = math.floor(x + 1), math.floor(y), math.floor(z)
    host("command", command=f"fill {bx} {by} {bz} {bx} {by + 2} {bz} minecraft:stone")
    guest.wait(10)
    before = host("state")["player"]["health"]
    guest.raw("mouse", "left", "click")
    guest.wait(25)
    after = host("state")["player"]["health"]
    assert after == before, ("attack through wall", before, after)
    results["wall_blocks_attack"] = True
    host("command", command=f"fill {bx} {by} {bz} {bx} {by + 2} {bz} minecraft:air")

    bind_attacks(guest, out)
    for label, words, allowed in (("rebound_mainhand", ["key", "r", "tap"], True),
                                  ("rebound_offhand", ["key", "v", "tap"], True),
                                  ("old_binding_inactive", ["mouse", "left", "click"], False)):
        prepare_duel(host, guest)
        before = host("state")["player"]["health"]
        guest.raw(*words)
        guest.wait(25)
        after = host("state")["player"]["health"]
        assert (after < before) if allowed else (after == before), (label, before, after)
        results[label] = {"before": before, "after": after}

    results.update(visual_check(host, guest, out, "key r tap", "key v tap"))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--ctl", type=Path, required=True)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ROOT / "native/.horizon-source")
    parser.add_argument("--out", type=Path, default=ROOT / "target/multiplayer-smoke")
    parser.add_argument("--visual-only", action="store_true", help="recapture animation views without repeating combat assertions")
    parser.add_argument("--installed-content", type=Path,
                        help="load this content .hmod through the normal mods folder")
    args = parser.parse_args()
    for binary in (args.client, args.ctl):
        if not binary.is_file():
            parser.error(f"missing executable {binary}")
    if args.installed_content and not args.installed_content.is_file():
        parser.error(f"missing content package {args.installed_content}")
    for report in ("horizon-resources.json", "registries.json", "commands.json"):
        if not (args.resources / report).is_file():
            parser.error(f"missing prepared resource {report}")
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    resources = args.out / "resources"
    # Explicit copies isolate caches and generated content overlays too.
    snapshot = args.out / "resource-snapshot.json"
    source = {
        "path": str(args.resources.resolve()),
        "manifest": hashlib.sha256((args.resources / "horizon-resources.json").read_bytes()).hexdigest(),
    }
    recorded = json.loads(snapshot.read_text()) if snapshot.is_file() else None
    if recorded != source or not (resources / "commands.json").is_file():
        shutil.copytree(args.resources, resources, dirs_exist_ok=True)
        snapshot.write_text(json.dumps(source, indent=2) + "\n")
    sys.path.insert(0, str(args.source.resolve() / "tools"))
    import lan_e2e

    original_raw = lan_e2e.Game.raw

    def raw(game, *words):
        if words and words[0] == "launch":
            words = (*words, "--game", str(args.client.resolve()),
                     "--resources", str(resources))
            if args.installed_content:
                home = Path(game.d.env["HORIZON_HOME"])
                mods = home / "horizon-mods"
                mods.mkdir(exist_ok=True)
                shutil.copyfile(args.installed_content, mods / args.installed_content.name)
                (home / "horizon-mods.txt").write_text("mod.combat_overhaul:true\n")
            else:
                words = (*words, "--dev-mod", str(ROOT / "content"))
        return original_raw(game, *words)

    lan_e2e.Game.raw = raw
    lan_e2e.CHECK_FNS["combat_overhaul"] = visual_check if args.visual_only else combat_check
    os.environ["HORIZON_E2E_HEADLESS"] = "1"
    results = lan_e2e.run(args.ctl.resolve(), args.out, resources, ["combat_overhaul"])
    report = "visual-results.json" if args.visual_only else "results.json"
    (args.out / report).write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))
    return 0 if results and all(result["pass"] for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
