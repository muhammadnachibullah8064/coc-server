import os
import json
from datetime import datetime, timedelta, timezone

import firebase_admin
from firebase_admin import credentials, firestore


# ---------- FIREBASE INIT (FROM ENV VARIABLE) ----------
firebase_json = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT"))

cred = credentials.Certificate(firebase_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()


# ---------- DELETE GLOBAL MESSAGES (7 DAYS) ----------
def delete_old_global_messages():
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    docs = db.collection("global_messages").where("createdAt", "<", cutoff).stream()

    deleted = 0

    for doc in docs:
        doc.reference.delete()
        deleted += 1

    print(f"[GLOBAL] Deleted {deleted} old messages")

    return deleted


# ---------- DELETE CLAN MESSAGES (30 DAYS) ----------
def delete_old_clan_messages():
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    clans = db.collection("clans").stream()

    deleted = 0

    for clan in clans:

        messages = (
            db.collection("clans")
            .document(clan.id)
            .collection("messages")
            .where("createdAt", "<", cutoff)
            .stream()
        )

        for msg in messages:
            msg.reference.delete()
            deleted += 1

    print(f"[CLAN] Deleted {deleted} old messages")

    return deleted


# ---------- MAIN ----------
def run_cleanup():
    print("Running Firestore chat cleanup...")

    g = delete_old_global_messages()
    c = delete_old_clan_messages()

    print(f"Cleanup finished. Global={g}, Clan={c}")


if __name__ == "__main__":
    run_cleanup()
