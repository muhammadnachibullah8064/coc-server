from fastapi import APIRouter
import json
import requests
import os
from dotenv import load_dotenv

router = APIRouter()

load_dotenv()
TOKEN = os.getenv("COC_API_TOKEN")

BASE = "https://api.clashofclans.com/v1"

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}


# ---------- GET SAVED ACTIVE LOCATIONS ----------
@router.get("/locations/active")
def active_locations():

    try:
        with open("active_locations.json") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = []

    return {
        "count": len(data),
        "locations": data
    }


# ---------- SCAN ACTIVE LOCATIONS ----------
@router.get("/locations/active/scan")
def scan_active_locations():

    r = requests.get(f"{BASE}/locations", headers=HEADERS, timeout=10)
    locations = r.json().get("items", [])

    active = []

    for loc in locations:

        loc_id = loc["id"]

        try:
            data = requests.get(
                f"{BASE}/locations/{loc_id}/rankings/players",
                headers=HEADERS,
                timeout=10
            ).json()

            if data.get("items"):
                active.append({
                    "id": loc_id,
                    "name": loc["name"]
                })

        except:
            continue

    with open("active_locations.json", "w") as f:
        json.dump(active, f)

    return {
        "status": "scan complete",
        "active_count": len(active)
    }
