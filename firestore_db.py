import os
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Render environment variable থেকে JSON key নেওয়া
firebase_key = os.getenv("FIREBASE_SERVICE_ACCOUNT")

if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(firebase_key))
    firebase_admin.initialize_app(cred)

db = firestore.client()
