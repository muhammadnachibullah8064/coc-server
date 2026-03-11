from fastapi import APIRouter
import json
import requests
import os

router = APIRouter()

# your render server base url
BASE_URL = os.getenv("PUBLIC_BASE_URL")


# ---------------- Active Locations ----------------
# Returns saved active locations from JSON file

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


# ---------------- Scan Active Locations ----------------
# Scans all locations and detects which ones have player rankings

@router.get("/locations/active/scan")
def scan_active_locations():

    r = requests.get(f"{BASE_URL}/locations")
    locations = r.json().get("items", [])

    active = []

    for loc in locations:

        loc_id = loc["id"]

        try:
            data = requests.get(
                f"{BASE_URL}/top/players/{loc_id}"
            ).json()

            if data.get("items"):
                active.append({
                    "id": loc_id,
                    "name": loc["name"]
                })

        except:
            pass

    with open("active_locations.json", "w") as f:
        json.dump(active, f)

    return {
        "status": "scan complete",
        "active_count": len(active)
    }
