"""Generate original vanilla-style weapons from the shared design catalogue.

Requires Pillow. Run from any directory with `python tools/generate_content.py`.
The polygons are authored in weapon-local pixel coordinates. Minecraft's
handheld model extrudes the resulting 16x16 sprites just like vanilla swords.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
NAMESPACE = "combat_overhaul"

# Each polygon uses (distance along handle, distance across handle).
# Separate silhouettes preserve each weapon's identity at inventory resolution.
SHAPES = {
    "dagger": [(4, -1), (8, -1), (10, 0), (8, 1), (4, 1)],
    "short_sword": [(4, -1), (10, -1), (12, 0), (10, 1), (4, 1)],
    "arming_sword": [(4, -1.3), (12, -1.3), (14, 0), (12, 1.3), (4, 1.3)],
    "longsword": [(5, -1), (14, -1), (16, 0), (14, 1), (5, 1)],
    "greatsword": [(6, -1.8), (14, -1.8), (17, 0), (14, 1.8), (6, 1.8)],
    "rapier": [(4, -0.45), (16, 0), (4, 0.45)],
    "estoc": [(5, -0.65), (13, -0.65), (17, 0), (13, 0.65), (5, 0.65)],
    "cutlass": [(4, -1), (9, -1), (13, -3), (12, 0), (9, 1.7), (4, 1.7)],
    "saber": [(4, -0.8), (10, -0.8), (15, -2.2), (13, 0), (10, 1), (4, 1)],
    "scimitar": [(4, -0.6), (9, -1), (13, -4), (14, -1), (11, 2), (4, 1)],
    "katana": [(5, -0.6), (12, -0.6), (16, -1.7), (15, 0), (11, 0.9), (5, 0.9)],
    "spear": [(11, 0), (13, -1.5), (17, 0), (13, 1.5)],
    "pike": [(13, -0.7), (18, 0), (13, 0.7)],
    "halberd": [(10, -0.6), (12, -0.6), (13, -4), (16, -2), (14, -0.5), (18, 0), (14, 0.7), (13, 3), (12, 0.7), (10, 0.7)],
    "glaive": [(10, -0.6), (13, -0.6), (17, -2), (17, 0), (14, 2), (11, 1.5)],
    "battleaxe": [(8, -0.8), (9, -3.8), (13, -3.8), (12, -1), (14, 0), (12, 1), (13, 3.8), (9, 3.8), (8, 0.8)],
    "warhammer": [(9, -3.2), (13, -3.2), (13, 2), (12, 2), (11, 4), (10, 2), (9, 2)],
    "mace": [(8, -1), (9, -2.4), (12, -2.4), (14, 0), (12, 2.4), (9, 2.4), (8, 1)],
    "club": [(3, -0.8), (7, -1.7), (12, -2), (14, -1), (14, 1), (12, 2), (7, 1.7), (3, 0.8)],
    "sickle": [(7, -0.7), (11, -2), (14, -1), (15, 2), (13, 4), (10, 4), (12, 2.5), (12, 0.5), (10, 0), (7, 1)],
}
POLES = {"spear", "pike", "halberd", "glaive"}
LONG_GRIPS = {"longsword", "greatsword", "estoc", "katana"}
SWORDS = {"dagger", "short_sword", "arming_sword", *LONG_GRIPS, "rapier", "cutlass", "saber", "scimitar"}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def tint(color, factor):
    return tuple(min(255, round(channel * factor)) for channel in color)


def sprite(weapon, material):
    """Draw deliberately stepped pixels with a dark border and lit blade edge."""
    labels = Image.new("L", (16, 16))
    draw = ImageDraw.Draw(labels)

    def polygon(points, color):
        draw.polygon([(round(2 + 0.66 * (u + v)), round(14 - 0.66 * (u - v))) for u, v in points], fill=color)

    grip_end = 12 if weapon in POLES else 8 if weapon in {"battleaxe", "warhammer", "mace", "sickle"} else 5 if weapon in LONG_GRIPS else 3
    polygon([(0, -0.65), (grip_end, -0.65), (grip_end, 0.65), (0, 0.65)], 1)
    if weapon in SWORDS:
        guard = 5 if weapon in LONG_GRIPS else 3.5
        width = 2.6 if weapon == "greatsword" else 2
        polygon([(guard - 0.5, -width), (guard + 0.5, -width), (guard + 0.5, width), (guard - 0.5, width)], 2)
    if weapon in {"rapier", "cutlass"}:
        polygon([(0, 1), (1, 2.5), (3.5, 2.5), (4, 1.2), (3, 1.5), (1, 1.5)], 2)
    polygon(SHAPES[weapon], 2)
    base_hex = material["color"].lstrip("#")
    base = tuple(int(base_hex[offset:offset + 2], 16) for offset in (0, 2, 4))
    colors = {1: (117, 78, 43), 2: base}
    pixels = labels.load()
    output = Image.new("RGBA", labels.size)
    for y in range(16):
        for x in range(16):
            label = pixels[x, y]
            if not label:
                continue
            above = pixels[x, y - 1] if y else 0
            below = pixels[x, y + 1] if y < 15 else 0
            factor = 1.38 if not above else 0.55 if not below else 1.0
            if label == 1 and (x + y) % 3 == 0:
                factor *= 0.75
            output.putpixel((x, y), (*tint(colors[label], factor), 255))
    return output


def model(item, weapon):
    scale = 1.1 if weapon["id"] in POLES else 1.0
    return {
        "parent": "minecraft:item/handheld",
        "textures": {"layer0": f"{NAMESPACE}:item/{item}"},
        "display": {
            "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68 * scale] * 3},
            "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68 * scale] * 3},
            "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4, 0.5], "scale": [0.85 * scale] * 3},
            "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4, 0.5], "scale": [0.85 * scale] * 3},
        },
    }


def item_definition(weapon, material):
    damage = weapon["damage"] + material["damage_bonus"]
    return {
        "template": material["template"],
        "max_stack_size": 1,
        "components": {
            "minecraft:max_damage": material["durability"],
            "minecraft:attack_range": {
                "min_reach": 0.0,
                "max_reach": weapon["reach"],
                "min_creative_reach": 0.0,
                "max_creative_reach": weapon["reach"] + 2.0,
                "hitbox_margin": 0.0,
            },
            "minecraft:attribute_modifiers": [
                {"type": "minecraft:attack_damage", "id": "minecraft:base_attack_damage", "amount": damage - 1, "operation": "add_value", "slot": "mainhand"},
                {"type": "minecraft:attack_speed", "id": "minecraft:base_attack_speed", "amount": weapon["attack_speed"] - 4, "operation": "add_value", "slot": "mainhand"},
            ],
        },
    }


def recipe(item, weapon, material):
    if material["id"] == "netherite":
        return {
            "type": "minecraft:smithing_transform",
            "template": "minecraft:netherite_upgrade_smithing_template",
            "base": f"{NAMESPACE}:diamond_{weapon['id']}",
            "addition": "minecraft:netherite_ingot",
            "result": {"id": f"{NAMESPACE}:{item}", "count": 1},
        }
    return {
        "type": "minecraft:crafting_shaped",
        "category": "equipment",
        "pattern": weapon["recipe"],
        "key": {"M": material["ingredient"], "S": "minecraft:stick"},
        "result": {"id": f"{NAMESPACE}:{item}", "count": 1},
    }


def generate():
    design = json.loads((ROOT / "design/weapons.json").read_text(encoding="utf-8"))
    weapons, materials = design["weapons"], design["materials"]
    assert len(weapons) == 20 and len(materials) == 7
    assert set(SHAPES) == {weapon["id"] for weapon in weapons}
    CONTENT.mkdir(parents=True, exist_ok=True)
    (CONTENT / "horizon-mod.toml").write_text(
        'id = "combat_overhaul"\nname = "Combat Overhaul Arsenal"\nversion = "0.1.0"\n'
        'description = "140 craftable weapons across seven material tiers."\n'
        'authors = ["Horizon Combat Overhaul contributors"]\napi = "0.2"\nside = "both"\ncapabilities = ["registries"]\n', encoding="utf-8"
    )
    assets = CONTENT / "assets" / NAMESPACE
    data = CONTENT / "data" / NAMESPACE
    names, item_ids = {}, []
    preview = Image.new("RGB", (7 * 128 + 160, 20 * 76 + 60), "#22252b")
    preview_draw = ImageDraw.Draw(preview)
    font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 14) if Path("C:/Windows/Fonts/consola.ttf").exists() else ImageFont.load_default()
    for column, material in enumerate(materials):
        preview_draw.text((170 + column * 128, 20), material["name"], fill="#ece8de", font=font)
        for row, weapon in enumerate(weapons):
            item = f"{material['id']}_{weapon['id']}"
            item_ids.append(f"{NAMESPACE}:{item}")
            write_json(data / "horizon/item" / f"{item}.json", item_definition(weapon, material))
            write_json(data / "recipe" / f"{item}.json", recipe(item, weapon, material))
            write_json(assets / "models/item" / f"{item}.json", model(item, weapon))
            write_json(assets / "items" / f"{item}.json", {"model": {"type": "minecraft:model", "model": f"{NAMESPACE}:item/{item}"}})
            texture = sprite(weapon["id"], material)
            texture_path = assets / "textures/item" / f"{item}.png"
            texture_path.parent.mkdir(parents=True, exist_ok=True)
            texture.save(texture_path)
            names[f"item.{NAMESPACE}.{item}"] = f"{material['name']} {weapon['name']}"
            enlarged = texture.resize((64, 64), Image.Resampling.NEAREST)
            preview.paste(enlarged, (190 + column * 128, 48 + row * 76), enlarged)
            if column == 0:
                preview_draw.text((8, 70 + row * 76), weapon["name"], fill="#ece8de", font=font)
    names[f"itemGroup.{NAMESPACE}.arsenal"] = "Combat Overhaul"
    write_json(assets / "lang/en_us.json", names)
    write_json(data / "horizon/creative_tab/arsenal.json", {"title": "Combat Overhaul", "icon": f"{NAMESPACE}:diamond_arming_sword", "items": item_ids})
    write_json(data / "tags/item/weapons.json", {"replace": False, "values": item_ids})
    eligible = [f"{NAMESPACE}:{m['id']}_{w['id']}" for m in materials for w in weapons if w["offhand"]]
    write_json(data / "tags/item/offhand_weapons.json", {"replace": False, "values": eligible})
    preview_path = ROOT / "design/weapon-preview.png"
    preview.save(preview_path)
    print(f"Generated {len(item_ids)} item definitions, recipes, models and textures in {CONTENT}")
    print(f"Preview: {preview_path}")


if __name__ == "__main__":
    generate()
