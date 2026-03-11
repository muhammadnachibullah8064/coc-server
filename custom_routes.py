from fastapi import APIRouter
import requests
import os
from dotenv import load_dotenv
from firestore_db import db

router = APIRouter()

load_dotenv()
TOKEN = os.getenv("COC_API_TOKEN")

BASE = "https://api.clashofclans.com/v1"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}


# ---------- GET ACTIVE PLAYER LOCATIONS ----------
@router.get("/locations/active/players")
def active_player_locations():

    doc = db.collection("config").document("active_player_locations").get()

    if not doc.exists:
        return {"count": 0, "locations": []}

    data = doc.to_dict().get("locations", [])

    return {
        "count": len(data),
        "locations": data
    }


# ---------- GET ACTIVE CLAN LOCATIONS ----------
@router.get("/locations/active/clans")
def active_clan_locations():

    doc = db.collection("config").document("active_clan_locations").get()

    if not doc.exists:
        return {"count": 0, "locations": []}

    data = doc.to_dict().get("locations", [])

    return {
        "count": len(data),
        "locations": data
    }


# ---------- SCAN ACTIVE LOCATIONS ----------
@router.get("/locations/active/scan")
def scan_active_locations():

    r = requests.get(f"{BASE}/locations", headers=HEADERS, timeout=10)
    locations = r.json().get("items", [])

    active_players = []
    active_clans = []

    for loc in locations:

        loc_id = loc["id"]
        loc_name = loc["name"]

        # ----- PLAYER CHECK -----
        try:
            data = requests.get(
                f"{BASE}/locations/{loc_id}/rankings/players",
                headers=HEADERS,
                timeout=10
            ).json()

            if data.get("items"):
                active_players.append({
                    "id": loc_id,
                    "name": loc_name
                })

        except:
            pass

        # ----- CLAN CHECK -----
        try:
            data = requests.get(
                f"{BASE}/locations/{loc_id}/rankings/clans",
                headers=HEADERS,
                timeout=10
            ).json()

            if data.get("items"):
                active_clans.append({
                    "id": loc_id,
                    "name": loc_name
                })

        except:
            pass

    # 🔥 Save to Firestore
    db.collection("config").document("active_player_locations").set({
        "locations": active_players
    })

    db.collection("config").document("active_clan_locations").set({
        "locations": active_clans
    })

    return {
        "status": "scan complete",
        "player_locations": len(active_players),
        "clan_locations": len(active_clans)
    }
