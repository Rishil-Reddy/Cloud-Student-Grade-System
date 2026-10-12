```python
import os
import json
from functools import wraps

from flask import request, jsonify, g
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud import firestore as google_firestore

load_dotenv()


def initialize_firebase():
    """Initialize Firebase Admin SDK using Render credentials or ADC."""
    if firebase_admin._apps:
        return

    project_id = os.getenv(
        "GCP_PROJECT_ID",
        "cloud-student-grade-system"
    )

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_JSON is invalid."
            ) from exc
    else:
        # Useful when running locally with Application Default Credentials.
        cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(
        cred,
        {"projectId": project_id}
    )


initialize_firebase()


def get_db():
    """Return the Firestore client for the configured project."""
    project_id = os.getenv(
        "GCP_PROJECT_ID",
        "cloud-student-grade-system"
    )

    emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST")

    if emulator_host:
        return google_firestore.Client(project=project_id)

    return firestore.client()


def require_auth(f):
    """Verify the Firebase ID token and load the user's profile."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Unauthorized",
                "message": "Missing or invalid Authorization header."
            }), 401

        token = auth_header[len("Bearer "):].strip()

        if not token:
            return jsonify({
                "error": "Unauthorized",
                "message": "Missing Firebase ID token."
            }), 401

        # Verify the Firebase ID token.
        try:
            decoded_token = auth.verify_id_token(token)
        except Exception:
            return jsonify({
                "error": "Unauthorized",
                "message": "Authentication failed. Please sign in again."
            }), 401

        uid = decoded_token.get("uid")

        if not uid:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid user token."
            }), 401

        # Load the user profile from Firestore.
        # Database failures should not be reported as invalid tokens.
        try:
            db = get_db()
            user_doc = db.collection("users").document(uid).get()
        except Exception:
            return jsonify({
                "error": "Service Unavailable",
                "message": "Unable to access the user profile."
            }), 503

        if not user_doc.exists:
            return jsonify({
                "error": "Forbidden",
                "message": "User profile not found."
            }), 403

        user_data = user_doc.to_dict() or {}

        if not user_data.get("is_active", True):
            return jsonify({
                "error": "Forbidden",
                "message": "Account has been deactivated."
            }), 403

        role = user_data.get("role")

        if role not in ("admin", "teacher", "student"):
            return jsonify({
                "error": "Forbidden",
                "message": "User role is missing or invalid."
            }), 403

        g.user = decoded_token
        g.uid = uid
        g.role = role
        g.user_data = {
            **user_data,
            "uid": uid,
            "email": user_data.get(
                "email",
                decoded_token.get("email", "")
            ),
            "role": role
        }

        return f(*args, **kwargs)

    return decorated_function


def require_role(allowed_roles):
    """Restrict an endpoint to one or more authorized roles."""

    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):

        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if getattr(g, "role", None) not in allowed_roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": (
                        "You do not have permission to access "
                        "this resource."
                    )
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
```
