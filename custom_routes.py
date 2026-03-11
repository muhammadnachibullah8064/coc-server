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


# ---------- GET PLAYER LOCATION LIST ----------
@router.get("/locations/active/players")
def active_player_locations():

    doc = db.collection("config").document("location_scan").get()

    if not doc.exists:
        return {
            "active_count": 0,
            "empty_count": 0,
            "active": [],
            "empty": []
        }

    data = doc.to_dict()

    return {
        "active_count": len(data.get("player_active", [])),
        "empty_count": len(data.get("player_empty", [])),
        "active": data.get("player_active", []),
        "empty": data.get("player_empty", [])
    }


# ---------- GET CLAN LOCATION LIST ----------
@router.get("/locations/active/clans")
def active_clan_locations():

    doc = db.collection("config").document("location_scan").get()

    if not doc.exists:
        return {
            "active_count": 0,
            "empty_count": 0,
            "active": [],
            "empty": []
        }

    data = doc.to_dict()

    return {
        "active_count": len(data.get("clan_active", [])),
        "empty_count": len(data.get("clan_empty", [])),
        "active": data.get("clan_active", []),
        "empty": data.get("clan_empty", [])
    }


# ---------- SCAN LOCATIONS ----------
@router.get("/locations/active/scan")
def scan_active_locations():

    r = requests.get(f"{BASE}/locations", headers=HEADERS, timeout=10)
    locations = r.json().get("items", [])

    player_active = []
    player_empty = []

    clan_active = []
    clan_empty = []

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
                player_active.append({
                    "id": loc_id,
                    "name": loc_name
                })
            else:
                player_empty.append({
                    "id": loc_id,
                    "name": loc_name
                })

        except:
            player_empty.append({
                "id": loc_id,
                "name": loc_name
            })

        # ----- CLAN CHECK -----
        try:
            data = requests.get(
                f"{BASE}/locations/{loc_id}/rankings/clans",
                headers=HEADERS,
                timeout=10
            ).json()

            if data.get("items"):
                clan_active.append({
                    "id": loc_id,
                    "name": loc_name
                })
            else:
                clan_empty.append({
                    "id": loc_id,
                    "name": loc_name
                })

        except:
            clan_empty.append({
                "id": loc_id,
                "name": loc_name
            })

    # 🔥 Save everything in ONE document
    db.collection("config").document("location_scan").set({

        "player_active": player_active,
        "player_empty": player_empty,

        "clan_active": clan_active,
        "clan_empty": clan_empty
    })

    return {
        "status": "scan complete",

        "player_active": len(player_active),
        "player_empty": len(player_empty),

        "clan_active": len(clan_active),
        "clan_empty": len(clan_empty)
    }
