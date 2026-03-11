from fastapi import APIRouter
import json

router = APIRouter()


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
