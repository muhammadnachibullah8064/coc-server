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


# ---------- GET SAVED ACTIVE LOCATIONS ----------
# Firestore থেকে active location list পড়বে
@router.get("/locations/active")
def active_locations():

    doc = db.collection("config").document("active_locations").get()

    if not doc.exists:
        return {
            "count": 0,
            "locations": []
        }

    data = doc.to_dict().get("locations", [])

    return {
        "count": len(data),
        "locations": data
    }


# ---------- SCAN ACTIVE LOCATIONS ----------
# Supercell API scan করে active locations Firestore এ save করবে
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

    # 🔥 Firestore save
    db.collection("config").document("active_locations").set({
        "locations": active
    })

    return {
        "status": "scan complete",
        "active_count": len(active)
    }
