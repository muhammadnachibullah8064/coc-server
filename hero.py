import json
from pathlib import Path
from typing import Dict, Tuple, Optional

# path to hero.json (same folder)
DATA_PATH = Path(__file__).parent / "hero.json"


def load_hero_data() -> Dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def add_time(total_hours: int, days: int, hours: int) -> int:
    return total_hours + days * 24 + hours


def hours_to_days_hours(total_hours: int) -> Tuple[int, int]:
    days = total_hours // 24
    hours = total_hours % 24
    return days, hours


def normalize_cost(data: Dict) -> Tuple[Optional[str], int]:
    if "dark" in data:
        return "dark", data["dark"]
    if "elixir" in data:
        return "elixir", data["elixir"]
    if "builder_elixir" in data:
        return "builder_elixir", data["builder_elixir"]
    return None, 0


def calc_hero(hero_name: str, current_level: int, max_level: int, hero_data: Dict) -> Dict:
    """
    Returns:
    {
      current: int,
      max: int,
      remainingLevels: int,
      time: { days: int, hours: int },
      cost: { type: str | None, amount: int },
      levels: {
        "96": { days, hours, cost },
        ...
      }
    }
    """
    total_hours = 0
    remaining_levels = 0
    total_cost = 0
    cost_type: Optional[str] = None
    levels: Dict = {}

    hero_levels = hero_data.get(hero_name, {})

    for target_level in range(current_level + 1, max_level + 1):
        key = str(target_level)
        if key not in hero_levels:
            continue

        t = hero_levels[key]

        # time
        total_hours = add_time(
            total_hours,
            t.get("days", 0),
            t.get("hours", 0),
        )

        # cost
        r_type, amount = normalize_cost(t)
        if r_type:
            cost_type = cost_type or r_type
            total_cost += amount

        # per-level details (for expand UI)
        levels[key] = {
            "days": t.get("days", 0),
            "hours": t.get("hours", 0),
            "cost": amount,
        }

        remaining_levels += 1

    days, hours = hours_to_days_hours(total_hours)

    return {
        "current": current_level,
        "max": max_level,
        "remainingLevels": remaining_levels,
        "time": {
            "days": days,
            "hours": hours,
        },
        "cost": {
            "type": cost_type,
            "amount": total_cost,
        },
        "levels": levels,
    }


# 🔎 quick local test
if __name__ == "__main__":
    data = load_hero_data()
    print(
        calc_hero(
            hero_name="Barbarian King",
            current_level=92,
            max_level=105,
            hero_data=data,
        )
    )
