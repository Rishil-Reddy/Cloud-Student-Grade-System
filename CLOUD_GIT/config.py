import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    PROJECT_ID = os.getenv("GCP_PROJECT_ID", "cloud-student-grade-system")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Emulators are disabled unless explicitly configured.
    FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST")
    FIREBASE_AUTH_EMULATOR_HOST = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")

    # Set emulator variables only when explicitly supplied.
    if FIRESTORE_EMULATOR_HOST:
        os.environ["FIRESTORE_EMULATOR_HOST"] = FIRESTORE_EMULATOR_HOST
    else:
        os.environ.pop("FIRESTORE_EMULATOR_HOST", None)

    if FIREBASE_AUTH_EMULATOR_HOST:
        os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = FIREBASE_AUTH_EMULATOR_HOST
    else:
        os.environ.pop("FIREBASE_AUTH_EMULATOR_HOST", None)

    os.environ["GCLOUD_PROJECT"] = PROJECT_ID

    DEFAULT_GRADE_SCALE = [
        {"min_score": 90.0, "max_score": 100.0, "grade": "O", "grade_points": 10.0, "is_pass": True, "description": "Outstanding"},
        {"min_score": 80.0, "max_score": 89.99, "grade": "A+", "grade_points": 9.0, "is_pass": True, "description": "Excellent"},
        {"min_score": 70.0, "max_score": 79.99, "grade": "A", "grade_points": 8.0, "is_pass": True, "description": "Very Good"},
        {"min_score": 60.0, "max_score": 69.99, "grade": "B+", "grade_points": 7.0, "is_pass": True, "description": "Good"},
        {"min_score": 50.0, "max_score": 59.99, "grade": "B", "grade_points": 6.0, "is_pass": True, "description": "Above Average"},
        {"min_score": 40.0, "max_score": 49.99, "grade": "C", "grade_points": 5.0, "is_pass": True, "description": "Pass"},
        {"min_score": 0.0, "max_score": 39.99, "grade": "F", "grade_points": 0.0, "is_pass": False, "description": "Fail"}
    ]
