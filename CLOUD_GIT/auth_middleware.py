import os
from functools import wraps
from flask import request, jsonify, g
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import auth, credentials, firestore

from google.cloud import firestore as google_firestore

load_dotenv()

# Explicitly ensure emulator environment variables are set
if os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
    os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")
if os.getenv("FIRESTORE_EMULATOR_HOST"):
    os.environ["FIRESTORE_EMULATOR_HOST"] = os.getenv("FIRESTORE_EMULATOR_HOST")

# Initialize Firebase Admin app
def initialize_firebase():
    if not firebase_admin._apps:
        project_id = os.getenv("GCP_PROJECT_ID", "demo-student-result-system")
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {'projectId': project_id})
        except Exception:
            firebase_admin.initialize_app(options={'projectId': project_id})

initialize_firebase()

def get_db():
    """Returns initialized Firestore client."""
    project_id = os.getenv("GCP_PROJECT_ID", "demo-student-result-system")
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        return google_firestore.Client(project=project_id)
    return firestore.client()

def require_auth(f):
    """
    Middleware that verifies Firebase Bearer token and attaches user info to Flask request context (g.user).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized", "message": "Missing or invalid Authorization header"}), 401
            
        token = auth_header.split("Bearer ")[1].strip()
        try:
            # Verify ID token with Firebase Auth (or emulator)
            decoded_token = auth.verify_id_token(token)
            g.user = decoded_token
            g.uid = decoded_token.get("uid")
            
            # Fetch user document from Firestore to get canonical role and active status
            db = get_db()
            user_doc = db.collection("users").document(g.uid).get()
            if not user_doc.exists:
                # If claims exist in token, fallback to token claims
                g.role = decoded_token.get("role", "student")
                g.user_data = {
                    "uid": g.uid,
                    "email": decoded_token.get("email", ""),
                    "name": decoded_token.get("name", "User"),
                    "role": g.role,
                    "is_active": True
                }
            else:
                user_data = user_doc.to_dict()
                if not user_data.get("is_active", True):
                    return jsonify({"error": "Forbidden", "message": "Account has been deactivated"}), 403
                g.role = user_data.get("role", "student")
                g.user_data = user_data
                
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Unauthorized", "message": f"Token verification failed: {str(e)}"}), 401
            
    return decorated_function

def require_role(allowed_roles):
    """
    Decorator to restrict endpoint access to specific roles (e.g. ['admin'], ['admin', 'teacher']).
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
                    "message": f"Insufficient permissions. Required one of: {allowed_roles}, your role: {user_role}"
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator
