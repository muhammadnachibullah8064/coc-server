import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# load env
load_dotenv()

COC_TOKEN = os.getenv("COC_API_TOKEN")
if not COC_TOKEN:
    raise RuntimeError("COC_API_TOKEN not found in .env")

COC_BASE = "https://api.clashofclans.com/v1"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {COC_TOKEN}",
}

app = FastAPI(
    title="COC Mini Server",
    version="1.0",
)


## NEW URL SYSTEM
@app.get("/app-config")
def app_config():
    return {
        "baseUrl": os.getenv("PUBLIC_BASE_URL"),
        "version": "1.0.0",
        "maintenance": False,
    }


# ---------------- utils ----------------
def normalize_tag(tag: str) -> str:
    """
    Accept:
    #ABC123
    ABC123
    %23ABC123
    """
    tag = tag.strip().upper()
    if tag.startswith("%23"):
        return tag
    if tag.startswith("#"):
        return "%23" + tag[1:]
    return "%23" + tag


def coc_get(path: str):
    url = f"{COC_BASE}{path}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        raise HTTPException(
            status_code=r.status_code,
            detail=(
                r.json()
                if r.headers.get("content-type", "").startswith("application/json")
                else r.text
            ),
        )
    return r.json()


# ---------------- routes ----------------


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/player/{tag}")
def get_player(tag: str):
    tag = normalize_tag(tag)
    data = coc_get(f"/players/{tag}")
    return JSONResponse(data)


@app.get("/clan/{tag}")
def get_clan(tag: str):
    tag = normalize_tag(tag)
    data = coc_get(f"/clans/{tag}")
    return JSONResponse(data)


# ---------------- current war ----------------


@app.get("/currentwar/{tag}")
def get_current_war(tag: str):
    tag_norm = normalize_tag(tag)

    try:
        data = coc_get(f"/clans/{tag_norm}/currentwar")
        return JSONResponse(data)

    except HTTPException as e:
        # Clan not in war → nicer response
        if e.status_code == 404:
            return {"state": "notInWar"}
        raise e


# ---------------- hero routes ----------------


@app.get("/hero/{tag}")
def get_hero(tag: str):
    tag_norm = normalize_tag(tag)

    # reuse existing player endpoint logic
    player = coc_get(f"/players/{tag_norm}")

    heroes_out = {}

    for h in player.get("heroes", []):
        heroes_out[h["name"]] = {
            "level": h.get("level", 0),
            "max": h.get("maxLevel", 0),
        }

    return {
        "tag": tag_norm.replace("%23", "#"),
        "heroes": heroes_out,
    }


# ---------------- hero calculation route ----------------
from hero import load_hero_data, calc_hero

# load once (startup time)
_HERO_DATA = load_hero_data()

HOME_HEROES = [
    "Barbarian King",
    "Archer Queen",
    "Grand Warden",
    "Royal Champion",
    "Minion Prince",
]

BUILDER_HEROES = [
    "Battle Machine",
    "Battle Copter",
]


@app.get("/hero/calc/{tag}")
def hero_calc(tag: str):
    tag_norm = normalize_tag(tag)

    # reuse existing Supercell call
    player = coc_get(f"/players/{tag_norm}")

    heroes = player.get("heroes", [])

    result = {
        "tag": tag_norm.replace("%23", "#"),
        "home": {},
        "builder": {},
    }

    for h in heroes:
        name = h.get("name")
        current = h.get("level", 0)
        max_level = h.get("maxLevel", 0)

        calc = calc_hero(
            hero_name=name,
            current_level=current,
            max_level=max_level,
            hero_data=_HERO_DATA,
        )

        if name in HOME_HEROES:
            result["home"][name] = calc
        elif name in BUILDER_HEROES:
            result["builder"][name] = calc

    return result


# ---------------- equipment calculation route ----------------
from equipment_calc import calculate_equipment


@app.get("/hero/equipment/calc/{tag}")
def hero_equipment_calc(tag: str):
    tag = normalize_tag(tag)

    data = coc_get(f"/players/{tag}")
    hero_equipment = data.get("heroEquipment", [])

    result = calculate_equipment(hero_equipment)

    return {"tag": tag.replace("%23", "#"), "heroes": result}
