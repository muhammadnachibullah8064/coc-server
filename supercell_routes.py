import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from cleanup_chat import delete_old_global_messages, delete_old_clan_messages


# load env
load_dotenv()
CLEANUP_KEY = os.getenv("CLEANUP_KEY")

COC_TOKEN = os.getenv("COC_API_TOKEN")
if not COC_TOKEN:
    raise RuntimeError("COC_API_TOKEN not found in .env")

# 🔥 split tokens
TOKENS = [t.strip() for t in COC_TOKEN.split(",") if t.strip()]

COC_BASE = "https://api.clashofclans.com/v1"

# 🔥 token index
token_index = 0


def get_token():
    global token_index
    token = TOKENS[token_index]
    token_index = (token_index + 1) % len(TOKENS)
    return token


# 🔥 dynamic headers (আগের static না)
def get_headers():
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {get_token()}",
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
@app.api_route("/health", methods=["GET", "HEAD"])
def health(request: Request):
    return {"status": "ok"}


# ---------------- firestore clean ----------------
@app.get("/cleanup")
def cleanup_chat(key: str):

    if key != CLEANUP_KEY:
        return {"error": "unauthorized"}

    g = delete_old_global_messages()
    c = delete_old_clan_messages()

    return {
        "status": "cleanup done",
        "global_deleted": g,
        "clan_deleted": c,
        "total_deleted": g + c,
    }


# ---------------- Locations ----------------
@app.get("/locations")
def get_locations():
    try:
        data = coc_get("/locations")
        return JSONResponse(data)
    except HTTPException as e:
        raise e


# ---------------- Players ----------------
@app.get("/player/{tag}")
def get_player(tag: str):
    tag = normalize_tag(tag)
    data = coc_get(f"/players/{tag}")
    return JSONResponse(data)


# ---------------- Top Home Village Players ----------------
@app.get("/top/players/{location}")
def get_top_players(location: str):

    location = location.strip().lower()

    try:
        data = coc_get(f"/locations/{location}/rankings/players")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"error": "Invalid location or no data"}
        raise e


# ---------------- Top Builder Base Players ----------------
@app.get("/top/builder/players/{location}")
def get_top_builder_players(location: str):

    location = location.strip().lower()

    try:
        data = coc_get(f"/locations/{location}/rankings/players-builder-base")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"error": "Invalid location or no data"}
        raise e


# ---------------- clan ----------------
@app.get("/clan/{tag}")
def get_clan(tag: str):
    tag = normalize_tag(tag)
    data = coc_get(f"/clans/{tag}")
    return JSONResponse(data)


# ---------------- Top Home Village Clans ----------------
@app.get("/top/clans/{location}")
def get_top_clans(location: str):

    location = location.strip().lower()

    try:
        data = coc_get(f"/locations/{location}/rankings/clans")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"error": "Invalid location or no data"}
        raise e


# ---------------- Top Builder Base Clans ----------------
@app.get("/top/builder/clans/{location}")
def get_top_builder_clans(location: str):

    location = location.strip().lower()

    try:
        data = coc_get(f"/locations/{location}/rankings/clans-builder-base")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"error": "Invalid location or no data"}
        raise e


# ---------------- Top Clan Capital Clans ----------------
@app.get("/top/capital/clans/{location}")
def get_top_capital_clans(location: str):

    location = location.strip().lower()

    try:
        data = coc_get(f"/locations/{location}/rankings/capitals")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"error": "Invalid location or no data"}
        raise e


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


# ---------------- CWL group ----------------
@app.get("/cwl/{tag}")
def get_cwl_group(tag: str):
    tag_norm = normalize_tag(tag)

    try:
        data = coc_get(f"/clans/{tag_norm}/currentwar/leaguegroup")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"state": "notInCWL"}
        raise e


# ---------------- CWL War By Tag ----------------
@app.get("/cwl/war/{warTag}")
def get_cwl_war(warTag: str):
    try:
        # warTag already looks like #ABC123
        warTag = normalize_tag(warTag)
        data = coc_get(f"/clanwarleagues/wars/{warTag}")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"error": "War not found"}
        raise e


# ---------------- Current Raid ----------------
# Clan এর চলমান (ongoing) raid weekend data ফেরত দেয়
@app.get("/raid/current/{tag}")
def get_current_raid(tag: str):

    # tag normalize (#ABC123 → %23ABC123)
    tag = normalize_tag(tag)

    # Supercell API call
    data = coc_get(f"/clans/{tag}/capitalraidseasons")

    # items এর ভিতরে raid list থাকে
    for raid in data.get("items", []):

        # শুধু ongoing raid খুঁজবে
        if raid.get("state") == "ongoing":
            return raid

    # যদি কোনো raid চলমান না থাকে
    return {"state": "noCurrentRaid"}


# ---------------- Raid History ----------------
# Clan এর শেষ হওয়া (ended) raid weekend history ফেরত দেয়
@app.get("/raid/history/{tag}")
def get_raid_history(tag: str):

    # tag normalize (#ABC123 → %23ABC123)
    tag = normalize_tag(tag)

    # Supercell API call
    data = coc_get(f"/clans/{tag}/capitalraidseasons")

    # শুধু ended raid গুলো filter করা
    ended_raids = [raid for raid in data.get("items", []) if raid.get("state") == "ended"]

    # history response
    return {"count": len(ended_raids), "items": ended_raids}


# ---------------- War History ----------------
@app.get("/warlog/{tag}")
def get_warlog(tag: str):
    tag_norm = normalize_tag(tag)

    try:
        data = coc_get(f"/clans/{tag_norm}/warlog")
        return JSONResponse(data)

    except HTTPException as e:
        if e.status_code == 404:
            return {"state": "noWarLog"}
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
    "Minion Prince",
    "Grand Warden",
    "Royal Champion",
    "Dragon Duke",
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
