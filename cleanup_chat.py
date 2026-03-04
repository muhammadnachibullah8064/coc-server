from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, firestore

# ---------- FIREBASE INIT ----------
cred = credentials.Certificate("serviceAccountKey.json")
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


# ---------- MAIN ----------
def run_cleanup():
    print("Running Firestore chat cleanup...")

    delete_old_global_messages()
    delete_old_clan_messages()

    print("Cleanup finished.")


if __name__ == "__main__":
    run_cleanup()
