"""import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
import uuid
from datetime import datetime

# ------------------------------------
# LOAD SERVICE ACCOUNT CREDENTIALS
# ------------------------------------
cred = credentials.Certificate("firebase_key.json")

# Initialize Firebase Admin (once)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# ------------------------------------
# EXPLICITLY PASS CREDENTIALS + DB NAME
# ------------------------------------
db = firestore.Client(
    project=cred.project_id,
    credentials=cred.get_credential(),
    database="resume"   # your Firestore database name
)

COLLECTION_NAME = "resume_sessions"

# ------------------------------------
# SESSION OPERATIONS
# ------------------------------------
def create_session(jd, weights):
    session_id = str(uuid.uuid4())
    db.collection(COLLECTION_NAME).document(session_id).set({
        "jd": jd,
        "weights": weights,
        "results": [],
        "created_at": datetime.utcnow().isoformat()
    })
    return session_id


def append_result(session_id, result):
    ref = db.collection(COLLECTION_NAME).document(session_id)
    ref.update({
        "results": firestore.ArrayUnion([result])
    })


def get_session(session_id):
    doc = db.collection(COLLECTION_NAME).document(session_id).get()
    return doc.to_dict() if doc.exists else None


def clear_session(session_id):
    db.collection(COLLECTION_NAME).document(session_id).delete()
"""
import uuid
from datetime import datetime
from google.cloud import firestore

# Firestore client (named DB)
db = firestore.Client(database="resume")

COLLECTION_NAME = "resume_sessions"


def create_session(jd: dict, weights: dict) -> str:
    session_id = str(uuid.uuid4())

    db.collection(COLLECTION_NAME).document(session_id).set({
        "jd": jd,
        "weights": weights,
        "results": [],
        "created_at": datetime.utcnow().isoformat()
    })

    return session_id


def append_result(session_id: str, result: dict) -> None:
    doc_ref = db.collection(COLLECTION_NAME).document(session_id)

    doc_ref.update({
        "results": firestore.ArrayUnion([result])
    })


def get_session(session_id: str) -> dict:
    doc = db.collection(COLLECTION_NAME).document(session_id).get()

    if not doc.exists:
        raise ValueError("Session not found")

    return doc.to_dict()


def clear_session(session_id: str) -> None:
    db.collection(COLLECTION_NAME).document(session_id).delete()
