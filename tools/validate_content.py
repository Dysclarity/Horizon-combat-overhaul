"""Validate the generated arsenal against its design without launching Horizon."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import tomllib

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RESOURCE_ID = re.compile(r"[a-z0-9_.-]+:[a-z0-9_./-]+\Z")
LARGE_WEAPONS = {"longsword", "greatsword", "rapier", "estoc", "katana",
                 "spear", "pike", "halberd", "glaive", "battleaxe"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def close(actual, expected, label):
    require(math.isfinite(actual) and math.isclose(actual, expected, abs_tol=1e-6),
            f"{label}: expected {expected}, found {actual}")


def canonical_recipe(recipe):
    rows = recipe["pattern"]
    require(1 <= len(rows) <= 3 and all(len(row) == len(rows[0]) for row in rows),
            "Recipe must be a rectangular grid with at most three rows")
    require(1 <= len(rows[0]) <= 3, "Recipe exceeds crafting grid width")
    occupied = [(x, y) for y, row in enumerate(rows) for x, char in enumerate(row) if char != " "]
    require(bool(occupied), "Empty crafting recipe")
    left, right = min(x for x, _ in occupied), max(x for x, _ in occupied)
    top, bottom = min(y for _, y in occupied), max(y for _, y in occupied)
    ingredients = recipe["key"]
    symbols = {char for row in rows for char in row if char != " "}
    require(symbols == set(ingredients), "Recipe has undefined or unused ingredient keys")
    grid = tuple(tuple(ingredients.get(char, " ") for char in row[left:right + 1])
                 for row in rows[top:bottom + 1])
    return min(grid, tuple(tuple(reversed(row)) for row in grid))


def validate(content, design):
    namespace = design["namespace"]
    materials, weapons = design["materials"], design["weapons"]
    require(len(weapons) == 20 and len({w["id"] for w in weapons}) == 20,
            "Expected twenty distinct weapon archetypes")
    require({m["id"] for m in materials} ==
            {"wood", "stone", "iron", "gold", "copper", "diamond", "netherite"},
            "Material roster differs from the seven requested tiers")
    manifest = tomllib.loads((content / "horizon-mod.toml").read_text(encoding="utf-8"))
    require(manifest["id"] == namespace and manifest["api"] == "0.2" and
            manifest["side"] == "both" and manifest["capabilities"] == ["registries"],
            "Content manifest does not match the arsenal")
    data, assets = content / "data" / namespace, content / "assets" / namespace
    expected = {f"{m['id']}_{w['id']}" for m in materials for w in weapons}
    for directory, extension in [(data / "horizon/item", ".json"), (data / "recipe", ".json"),
                                 (assets / "items", ".json"), (assets / "models/item", ".json"),
                                 (assets / "textures/item", ".png")]:
        found = {path.stem for path in directory.glob(f"*{extension}")}
        require(found == expected, f"{directory}: missing {sorted(expected - found)}, extra {sorted(found - expected)}")
    names = read_json(assets / "lang/en_us.json")
    texture_hashes, animation_hashes = set(), set()
    for weapon in weapons:
        frames = weapon["animation"]["keyframes"]
        require(all(len(frame) == 7 and all(math.isfinite(v) for v in frame) for frame in frames),
                f"{weapon['id']}: malformed animation keyframe")
        require(frames[0] == [0] * 7 and frames[-1] == [1] + [0] * 6,
                f"{weapon['id']}: animation does not start and end at rest")
        require(all(a[0] < b[0] for a, b in zip(frames, frames[1:])),
                f"{weapon['id']}: animation times are not strictly increasing")
        animation_hashes.add(json.dumps(frames))
    require(len(animation_hashes) == 20, "Weapon archetypes share identical animation keyframes")

    for material in materials:
        recipe_shapes, silhouettes = set(), set()
        for weapon in weapons:
            item = f"{material['id']}_{weapon['id']}"
            identifier = f"{namespace}:{item}"
            require(RESOURCE_ID.fullmatch(identifier), f"Invalid item identifier {identifier}")
            definition = read_json(data / "horizon/item" / f"{item}.json")
            require(definition["template"] == material["template"] and definition["max_stack_size"] == 1,
                    f"{item}: incorrect template or stack size")
            components = definition["components"]
            require(components["minecraft:max_damage"] == material["durability"], f"{item}: wrong durability")
            modifiers = components["minecraft:attribute_modifiers"]
            require(len(modifiers) == 2, f"{item}: duplicate or missing attack modifiers")
            attributes = {modifier["type"]: modifier for modifier in modifiers}
            for modifier in modifiers:
                require(modifier["operation"] == "add_value" and modifier["slot"] == "mainhand",
                        f"{item}: invalid modifier operation or slot")
            close(1 + attributes["minecraft:attack_damage"]["amount"],
                  weapon["damage"] + material["damage_bonus"], f"{item} damage")
            close(4 + attributes["minecraft:attack_speed"]["amount"], weapon["attack_speed"], f"{item} speed")
            attack_range = components["minecraft:attack_range"]
            close(attack_range["max_reach"], weapon["reach"], f"{item} reach")
            close(attack_range["max_creative_reach"], weapon["reach"] + 2, f"{item} creative reach")
            require(attack_range["min_reach"] == attack_range["min_creative_reach"] == 0,
                    f"{item}: unexpected minimum reach")
            require(names[f"item.{namespace}.{item}"] == f"{material['name']} {weapon['name']}",
                    f"{item}: missing or incorrect translated name")

            recipe = read_json(data / "recipe" / f"{item}.json")
            require(recipe["result"] == {"id": identifier, "count": 1}, f"{item}: incorrect recipe output")
            if material.get("smithing_base_material"):
                require(recipe["type"] == "minecraft:smithing_transform" and
                        recipe["base"] == f"{namespace}:{material['smithing_base_material']}_{weapon['id']}" and
                        recipe["addition"] == material["ingredient"] and
                        recipe["template"] == "minecraft:netherite_upgrade_smithing_template",
                        f"{item}: incorrect smithing upgrade")
            else:
                require(recipe["type"] == "minecraft:crafting_shaped" and
                        recipe["key"] == {"M": material["ingredient"], "S": "minecraft:stick"} and
                        recipe["pattern"] == weapon["recipe"], f"{item}: crafting recipe differs from design")
                shape = canonical_recipe(recipe)
                require(shape not in recipe_shapes, f"{item}: recipe collides after trimming or mirroring")
                recipe_shapes.add(shape)

            item_model = read_json(assets / "items" / f"{item}.json")["model"]
            require(item_model == {"type": "minecraft:model", "model": f"{namespace}:item/{item}"},
                    f"{item}: unresolved item model reference")
            model = read_json(assets / "models/item" / f"{item}.json")
            require(model["parent"] == "minecraft:item/handheld" and
                    model["textures"]["layer0"] == f"{namespace}:item/{item}",
                    f"{item}: incorrect parent or unresolved texture reference")
            for view in ["firstperson_righthand", "firstperson_lefthand", "thirdperson_righthand", "thirdperson_lefthand"]:
                transform = model["display"][view]
                require(all(len(transform[key]) == 3 and all(math.isfinite(v) for v in transform[key])
                            for key in ["rotation", "translation", "scale"]) and
                        all(v > 0 for v in transform["scale"]), f"{item}: invalid {view} transform")
            with Image.open(assets / "textures/item" / f"{item}.png") as texture:
                size = 32 if weapon["id"] in LARGE_WEAPONS else 16
                require(texture.format == "PNG" and texture.size == (size, size) and texture.mode == "RGBA",
                        f"{item}: expected a {size}x{size} RGBA PNG")
                texture.load()
                require(set(texture.getchannel("A").tobytes()) == {0, 255},
                        f"{item}: texture must contain transparent space and crisp opaque pixels")
                digest = hashlib.sha256(texture.tobytes()).digest()
                require(digest not in texture_hashes, f"{item}: duplicates another weapon texture")
                texture_hashes.add(digest)
                silhouette = texture.getchannel("A").tobytes()
                require(silhouette not in silhouettes, f"{item}: duplicates another archetype's silhouette")
                silhouettes.add(silhouette)

    all_ids = {f"{namespace}:{item}" for item in expected}
    offhand_ids = {f"{namespace}:{m['id']}_{w['id']}" for m in materials for w in weapons if w["offhand"]}
    for tag, expected_ids in [("weapons", all_ids), ("offhand_weapons", offhand_ids)]:
        values = read_json(data / "tags/item" / f"{tag}.json")["values"]
        require(len(values) == len(set(values)) and set(values) == expected_ids, f"Incorrect {tag} tag")
    tab = read_json(data / "horizon/creative_tab/arsenal.json")
    require(set(tab["items"]) == all_ids and len(tab["items"]) == 140 and tab["icon"] in all_ids,
            "Creative tab must expose every weapon exactly once with a valid icon")
    print(f"Validated {len(expected)} weapons, {len(offhand_ids)} offhand variants, 140 recipes, 140 models, 140 textures, and 20 animations.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--content", type=Path, default=ROOT / "content")
    args = parser.parse_args()
    try:
        validate(args.content, read_json(ROOT / "design/weapons.json"))
    except (ValueError, KeyError, OSError, TypeError) as error:
        print(f"Content validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
