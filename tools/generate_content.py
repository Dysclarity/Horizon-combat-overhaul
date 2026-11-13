"""Generate original vanilla-style weapons from the shared design catalogue.

Requires Pillow. Run from any directory with `python tools/generate_content.py`.
The polygons are authored in weapon-local pixel coordinates. Minecraft's
handheld model extrudes the original 16x16 and 32x32 sprites like vanilla swords.
"""

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
NAMESPACE = "combat_overhaul"

# Outlined silhouettes are authored at the destination pixel grid. Large weapons
# have their own geometry and detailing, rather than enlarged 16-pixel sprites.
LARGE_WEAPONS = {
    "longsword", "greatsword", "rapier", "estoc", "katana",
    "spear", "pike", "halberd", "glaive", "battleaxe",
}
POLES = {"spear", "pike", "halberd", "glaive"}

# Dark outline, shadow, body, bevel, edge. Deliberately chosen colour clusters
# keep iron neutral, gold warm, copper orange, diamond cyan and netherite dusky.
PALETTES = {
    "wood": ("392617", "624322", "94703d", "bc995c", "e2bf7e"),
    "stone": ("30302e", "575954", "83867f", "a8aca4", "c9cdc4"),
    "iron": ("343839", "656d70", "a0aaac", "cbd5d4", "edf6ed"),
    "gold": ("49340b", "94641b", "d6a72c", "f4d954", "fff2a2"),
    "copper": ("48271f", "874730", "c4774b", "eaa574", "ffd6a5"),
    "diamond": ("104440", "117b76", "2cb9ad", "65dfcf", "b9fff0"),
    "netherite": ("201c22", "3c323e", "625461", "897b89", "b3a5b1"),
}
SHAFT = ("302116", "513824", "7b5531", "a07846", "c4a16a")
LEATHER = ("291d18", "463027", "6c4835", "926844", "bc9363")

# Weapon-local longitudinal / transverse coordinates. A separate contour for
# every weapon preserves familiar real-world proportions and construction.
BLADES = {
    "dagger": [(4,-1.4),(8,-1.4),(11.5,0),(8,1.4),(4,1.4)],
    "short_sword": [(4,-1.6),(10.5,-1.6),(14,0),(10.5,1.6),(4,1.6)],
    "arming_sword": [(4,-1.8),(11,-1.8),(15,0),(11,1.8),(4,1.8)],
    "longsword": [(9,-1.5),(25,-1.5),(30,0),(25,1.5),(9,1.5)],
    "greatsword": [(10,-2.2),(25,-2.2),(30,0),(25,2.2),(10,2.2)],
    "rapier": [(7,-.65),(26,-.65),(30,0),(26,.65),(7,.65)],
    "estoc": [(8,-1.2),(20,-1),(30,0),(20,1),(8,1.2)],
    "cutlass": [(4,-1.2),(8,-1.2),(12,-2.4),(14,-2.5),(12,.1),(8,1.6),(4,1.6)],
    "saber": [(4,-.8),(9,-1),(13,-2),(15,-2),(13,-.2),(9,1),(4,1)],
    "scimitar": [(4,-.6),(8,-.9),(11,-2),(13,-3.4),(14,-3.8),(13,-1.2),(10,1),(7,1.6),(4,1.2)],
    "katana": [(9,-1),(18,-1),(25,-2),(29,-3),(30,-2.5),(27,-.6),(21,.6),(14,1.2),(9,1.2)],
    "spear": [(20,0),(24,-2.1),(30,0),(24,2.1)],
    "pike": [(25,-.8),(29,-1.2),(32,0),(29,1.2),(25,.8)],
    "halberd": [(19,-.8),(22,-1),(24,-4),(27,-6),(28,-5),(28,-2),(26,-1),(31,0),(26,.8),(25,4.5),(23,3),(24,1),(19,1)],
    "glaive": [(19,-.9),(24,-1),(29,-3.2),(31,-3.2),(30,-.3),(27,2),(23,2.5),(20,1.4)],
    "battleaxe": [(16,-1),(17,-4),(16,-6),(19,-8),(23,-7),(25,-5),(24,-3),(22,-2),(22,1),(19,1),(19,-1)],
    "warhammer": [(8,-3),(11,-3),(11,-.8),(10.8,1.2),(9.8,4.5),(8.8,1.2),(8,-.7)],
    "mace": [(7,-1),(8,-2.5),(10,-3),(12,-2),(13,0),(12,2),(10,3),(8,2.5),(7,1)],
    "club": [(4,-.8),(7,-1.5),(11,-2.1),(13,-1.3),(13,1),(11,2.2),(7,1.7),(4,.8)],
    "sickle": [(6,-1),(8,-3),(11,-4),(14,-2),(15,1),(13,3.5),(10,4),(12,2),(12,0),(10,-1),(8,-.5),(6,1)],
}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sprite(weapon, material):
    """Paint sharp pixel clusters, visible bevels and hand-wrapped grips."""
    size = 32 if weapon in LARGE_WEAPONS else 16
    scale = .84 if size == 32 else .7
    origin = (3, 28) if size == 32 else (2, 13)
    output = Image.new("RGBA", (size, size))
    metal = tuple(tuple(bytes.fromhex(c)) for c in PALETTES[material["id"]])
    wood = tuple(tuple(bytes.fromhex(c)) for c in SHAFT)
    leather = tuple(tuple(bytes.fromhex(c)) for c in LEATHER)

    def point(u, v):
        return round(origin[0] + scale*(u+v)), round(origin[1] - scale*(u-v))

    def shape(points, palette, details=()):
        # One-pixel outlines and shading are rasterized directly at 16 or 32.
        # The mask is binary throughout; no antialiasing or resampling occurs.
        mask = Image.new("L", (size, size))
        ImageDraw.Draw(mask).polygon([point(*p) for p in points], fill=255)
        outline = mask.filter(ImageFilter.MaxFilter(3))
        output.paste((*palette[0], 255), (0, 0), outline)
        pixels = mask.load()
        for y in range(size):
            for x in range(size):
                if not pixels[x, y]:
                    continue
                left = x > 0 and pixels[x-1, y]
                above = y > 0 and pixels[x, y-1]
                right = x+1 < size and pixels[x+1, y]
                below = y+1 < size and pixels[x, y+1]
                shade = 4 if not left else 3 if not above else 1 if not right or not below else 2
                output.putpixel((x, y), (*palette[shade], 255))
        detail = Image.new("RGBA", (size, size))
        pen = ImageDraw.Draw(detail)
        for points, shade in details:
            pen.line([point(*p) for p in points], fill=(*palette[shade],255), width=1)
        # Trim details to the material face so no bright pixel spills outside.
        detail.putalpha(ImageChops.multiply(detail.getchannel("A"), mask))
        output.alpha_composite(detail)

    def bar(start, end, half_width, palette, details=()):
        shape([(start,-half_width),(end,-half_width),(end,half_width),(start,half_width)], palette, details)

    shaft_end = {
        "spear": 24, "pike": 28, "halberd": 26, "glaive": 24,
        "battleaxe": 23, "warhammer": 10, "mace": 10, "sickle": 8,
    }.get(weapon, 9 if size == 32 else 4)
    bar(1, shaft_end, .75 if size == 16 else .9, wood,
        [([(2,-.35),(shaft_end-1,-.35)],3)])
    grip_end = 7 if weapon in {"longsword","greatsword","katana","estoc"} else 4 if size == 32 else 3
    if weapon in POLES or weapon == "battleaxe":
        grip_end = 8
    # Diagonal bands form a leather wrap; the wood continues above the grip.
    wrap = [([(u,-.8),(u+1,.8)],3) for u in range(2, int(grip_end), 2)]
    bar(1, grip_end, .85 if size == 16 else 1.1, leather, wrap)
    if weapon in {"dagger","short_sword","arming_sword","longsword","greatsword","estoc"}:
        guard = 8 if size == 32 else 4
        width = 4.5 if weapon == "greatsword" else 3.5 if size == 32 else 2.4
        shape([(guard-1,-width),(guard,-width),(guard+1,-1),(guard+1,1),(guard,width),(guard-1,width),(guard,0)], metal)
        bar(0, .8, 1.2 if size == 32 else .8, metal)
    elif weapon in {"rapier", "cutlass", "saber"}:
        guard = 7 if size == 32 else 4
        width = 3.2 if size == 32 else 2
        # Open knuckle bow with a small cup at the blade's base.
        shape([(1,.5),(1,2),(3,3),(guard-1,2.8),(guard+1,1),(guard,0),
               (guard-1,1.6),(3,2),(2,1.4)], metal)
        shape([(guard-1,-width),(guard+1,-width),(guard+1,1.5),(guard-1,1.5)], metal)
        if weapon == "rapier":
            shape([(5,-3),(7,-3),(8,-1),(7,1),(5,1),(4,-1)], metal)
            # A dark opening gives the swept hilt a readable pierced centre.
            ImageDraw.Draw(output).point(point(6,-1), fill=(*metal[0],255))
    elif weapon == "katana":
        # Compact tsuba and collar above a long, cross-wrapped grip.
        shape([(8,-2.1),(9,-2.1),(9,2.1),(8,2.1)], metal)
        bar(9,10,1.1,metal)
        for u in (2,4,6):
            ImageDraw.Draw(output).point(point(u,0), fill=(*leather[4],255))
    elif weapon == "scimitar":
        shape([(3,-2),(4,-2),(5,0),(4,2),(3,2),(4,0)],metal)
    else:
        bar(0,.5,.9,metal)

    details = []
    if weapon in {"short_sword","arming_sword","longsword","greatsword","estoc"}:
        start, end = (11,24) if size == 32 else (6,10)
        details += [([(start,0),(end,0)],1), ([(start,-.8),(end,-.8)],3)]
    if weapon == "rapier":
        details += [([(9,0),(27,0)],4)]
    if weapon == "katana":
        details += [([(11,.8),(20,.4),(26,-.7),(28,-1.8)],4),
                    ([(11,-.5),(20,-.6),(25,-1.5)],1)]
    if weapon in {"cutlass","saber","scimitar"}:
        details += [([(6,.6),(9,.2),(12,-1.4)],4)]
    if weapon == "spear":
        details += [([(23,0),(28,0)],1), ([(24,-1),(28,0)],4)]
    if weapon == "pike":
        details += [([(26,-.3),(30,0)],4)]
    if weapon == "glaive":
        details += [([(22,1),(26,1),(29,-.5)],4), ([(22,-.2),(26,-1)],1)]
    if weapon == "battleaxe":
        details += [([(17,-5),(19,-7),(22,-6),(24,-4)],4),
                    ([(19,-3),(21,-4),(23,-3)],1)]
    if weapon == "halberd":
        details += [([(25,-4),(27,-5),(27,-3)],4), ([(24,0),(29,0)],3)]
    if weapon == "warhammer":
        details += [([(8.5,-2),(10.5,-2)],4)]
    if weapon == "mace":
        # Alternating bevels read as forged flanges, not a spherical stone.
        details += [([(8,-1.8),(11,-1.8)],4), ([(8,0),(12,0)],1),
                    ([(8,1.7),(11,1.7)],3)]
    if weapon == "club":
        details += [([(6,-.3),(11,-.5)],1), ([(7,1),(11,1)],3)]
    if material["id"] == "wood":
        # Long grain follows the material instead of random pixel noise.
        details += [([(6,-.3),(8,-.3)],1)]
    elif material["id"] == "stone":
        details += [([(8,-.5),(9,.5)],1), ([(10,.8),(11,.8)],3)]
    shape(BLADES[weapon],metal,details)
    if weapon in POLES:
        # A socket and two iron bands attach the head to the wooden shaft.
        socket = 19 if weapon in {"halberd","glaive"} else 21 if weapon == "spear" else 25
        bar(socket-2,socket,.95,metal)
        bar(socket-5,socket-4,.95,metal)
    if weapon == "battleaxe":
        # Visible eye and reinforced haft, with a single cutting head.
        bar(18,21,.8,metal)
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
    assert set(BLADES) == {weapon["id"] for weapon in weapons}
    CONTENT.mkdir(parents=True, exist_ok=True)
    (CONTENT / "horizon-mod.toml").write_text(
        'id = "combat_overhaul"\nname = "Combat Overhaul Arsenal"\nversion = "0.1.1"\n'
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
