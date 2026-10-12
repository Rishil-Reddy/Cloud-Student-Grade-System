import os
from functools import wraps

from flask import request, jsonify, g
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud import firestore as google_firestore

load_dotenv()


# ==========================================
# FIREBASE INITIALIZATION
# ==========================================

def initialize_firebase():
    """Initialize Firebase Admin using valid application credentials."""
    if not firebase_admin._apps:
        project_id = os.getenv(
            "GCP_PROJECT_ID",
            "cloud-student-grade-system"
        )

        # Application Default Credentials must be configured
        # in the deployment environment.
        cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(
            cred,
            {"projectId": project_id}
        )


initialize_firebase()


# ==========================================
# FIRESTORE DATABASE
# ==========================================

def get_db():
    """Return the Firestore client for the configured project."""
    project_id = os.getenv(
        "GCP_PROJECT_ID",
        "cloud-student-grade-system"
    )

    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        return google_firestore.Client(project=project_id)

    return firestore.client()


# ==========================================
# AUTHENTICATION MIDDLEWARE
# ==========================================

def require_auth(f):
    """
    Verify the Firebase ID token and attach the authenticated
    user's information to the Flask request context.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Unauthorized",
                "message": "Missing or invalid Authorization header"
            }), 401

        token = auth_header[len("Bearer "):].strip()

        if not token:
            return jsonify({
                "error": "Unauthorized",
                "message": "Missing Firebase ID token"
            }), 401

        try:
            # Verify the Firebase ID token.
            decoded_token = auth.verify_id_token(token)

            uid = decoded_token.get("uid")
            if not uid:
                return jsonify({
                    "error": "Unauthorized",
                    "message": "Invalid user identity"
                }), 401

            g.user = decoded_token
            g.uid = uid

            # Retrieve the user's application profile.
            db = get_db()
            user_doc = db.collection("users").document(uid).get()

            # Do not grant access to accounts without a profile.
            if not user_doc.exists:
                return jsonify({
                    "error": "Forbidden",
                    "message": "User profile not found"
                }), 403

            user_data = user_doc.to_dict() or {}

            # Block deactivated accounts.
            if not user_data.get("is_active", True):
                return jsonify({
                    "error": "Forbidden",
                    "message": "Account has been deactivated"
                }), 403

            # Role comes from the Firestore profile, not token claims.
            role = user_data.get("role")

            if role not in ("admin", "teacher", "student"):
                return jsonify({
                    "error": "Forbidden",
                    "message": "User profile has an invalid role"
                }), 403

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

        except Exception:
            # Avoid exposing internal verification or database details.
            return jsonify({
                "error": "Unauthorized",
                "message": "Authentication failed. Please sign in again."
            }), 401

    return decorated_function


# ==========================================
# ROLE-BASED AUTHORIZATION
# ==========================================

def require_role(allowed_roles):
    """
    Restrict an endpoint to the specified application roles.
    Example: @require_role(["admin", "teacher"])
    """

    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):

        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = getattr(g, "role", None)

            if user_role not in allowed_roles:
                return jsonify({
                    "error": "Forbidden",
                    "message": "You do not have permission to access this resource."
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
