import json
from typing import Dict, Any

# ---------- load json files ----------
with open("equipment_ore.json", "r", encoding="utf-8") as f:
    EQUIP_ORE = json.load(f)

with open("equipment_hero_map.json", "r", encoding="utf-8") as f:
    HERO_MAP = json.load(f)


def find_hero_for_equipment(eq_name: str) -> str | None:
    for hero, eq_list in HERO_MAP.items():
        if eq_name in eq_list:
            return hero
    return None


def calculate_equipment(
    hero_equipment: list[Dict[str, Any]]
) -> Dict[str, Any]:

    result: Dict[str, Any] = {}

    for eq in hero_equipment:
        name = eq["name"]
        current = eq["level"]
        max_level = eq["maxLevel"]

        hero = find_hero_for_equipment(name)
        if not hero:
            continue

        if hero not in result:
            result[hero] = {}

        levels = {}
        total = {"shiny": 0, "glowy": 0, "starry": 0}

        ore_table = EQUIP_ORE.get(name, {})

        for lvl in range(current + 1, max_level + 1):
            lvl_key = str(lvl)
            if lvl_key not in ore_table:
                continue

            cost = ore_table[lvl_key]
            levels[lvl_key] = cost

            total["shiny"] += cost.get("shiny", 0)
            total["glowy"] += cost.get("glowy", 0)
            total["starry"] += cost.get("starry", 0)

        result[hero][name] = {
            "current": current,
            "max": max_level,
            "levels": levels,
            "total": total,
        }

    return result
