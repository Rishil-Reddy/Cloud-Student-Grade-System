# Student Result Management System (Cloud Computing Mini Project)

A secure, cloud-native Student Result Management System built with Python Flask, Google Cloud Firestore, Firebase Authentication with Role-Based Access Control (RBAC), and containerized for Google Cloud Run.

---

## 🌟 Key Features

- **Role-Based Access Control (RBAC)**:
  - **Admin**: Create and manage students, teachers, courses, semesters, and assign teachers to course offerings. View complete marks modification audit trail.
  - **Teacher**: Enter and update marks for assigned courses only, perform bulk CSV mark uploads with validation & error reporting, and view real-time class performance statistics.
  - **Student**: View only their own results, subject-wise grades, GPA/CGPA summary, and download verifiable PDF transcripts.
- **Configurable Grade Scale**: Stored dynamically in Firestore config rather than hard-coded in business logic.
- **Comprehensive Audit Trail**: Every score addition, update, and bulk upload logs who made the change, timestamp, old score, and new score.
- **Enterprise Security**:
  - Server-side role enforcement on every endpoint.
  - Strict student UID token isolation (preventing URL/parameter ID spoofing).
  - Rate limiting on sensitive routes.
  - Content Security Policy (CSP), X-Frame-Options (`DENY`), and security headers.
  - Firestore Security Rules matching role permissions.

---

## 🏗️ Tech Stack

- **Backend**: Python 3.11, Flask, Flask-Limiter, ReportLab (PDF), Gunicorn
- **Database**: Cloud Firestore (Emulator locally / Google Cloud Firestore in production)
- **Auth**: Firebase Authentication with custom role claims (Emulator locally)
- **Frontend**: Responsive Vanilla HTML5 / Modern Glassmorphic CSS / JavaScript SPA
- **Containerization & Cloud**: Docker, Google Cloud Run

---

## 🚀 Local Development Quickstart

### Prerequisites
1. **Python 3.11+**
2. **Node.js 18+** & Java 11+ (for running Firebase local emulators)
3. **Firebase CLI** (`npm install -g firebase-tools` or via `npx.cmd`)

### Step 1: Clone and Set Up Virtual Environment
```bash
# Clone the repository and navigate into it
cd "Cloud Computing Mini Project"

# Create and activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux / Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(In local emulator mode, no real API keys or Google Cloud credentials are needed)*

### Step 3: Start Firebase Emulators
In a separate terminal window:
```bash
npx.cmd firebase-tools emulators:start --only auth,firestore
```
The emulators will run at:
- **Firestore Emulator**: `http://127.0.0.1:8080`
- **Auth Emulator**: `http://127.0.0.1:9099`
- **Emulator UI**: `http://127.0.0.1:4000`

### Step 4: Seed Sample Database
Run the seed script to create initial roles, courses, and marks:
```bash
python seed_data.py
```

### Step 5: Start the Flask Application
```bash
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 👥 Demo Logins (Pre-seeded in Local Emulator)

| Role | Email | Password | Pre-assigned Courses / Info |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@university.edu` | `AdminPassword123!` | System Administrator |
| **Teacher** | `dr.smith@university.edu` | `TeacherPassword123!` | Assigned to **CS101** & **CS103** |
| **Teacher** | `prof.johnson@university.edu` | `TeacherPassword123!` | Assigned to **CS102** & **CS103** |
| **Student** | `alice@student.university.edu` | `StudentPassword123!` | Roll No: **STU2025001** (Spring 2025 results) |
| **Student** | `charlie@student.university.edu` | `StudentPassword123!` | Roll No: **STU2025003** (Spring 2025 results) |

---

## 🧪 Running Automated Unit & Security Tests

Run the test suite using `pytest`:
```bash
pytest -v
```
This tests:
1. Grade boundary calculation formulas and GPA/CGPA algorithms.
2. Unauthenticated request rejection (401).
3. Student blocked from Admin endpoints (403).
4. Teacher blocked from viewing/editing unassigned courses (403).
5. Student URL ID spoofing prevention (Server enforces token UID).

---

## ☁️ Google Cloud Run Deployment Guide

When you are ready to deploy the application to Google Cloud:

### Step 1: Create a Google Cloud Project & Enable APIs
```bash
# Set project
gcloud config set project [YOUR_PROJECT_ID]

# Enable necessary Google Cloud APIs
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

### Step 2: Set up Firestore in Cloud Console
1. Navigate to **Firestore** in the Google Cloud Console.
2. Click **Create Database** (Native Mode) and select your preferred region (e.g. `us-central1`).
3. Deploy Firestore security rules:
   ```bash
   firebase deploy --only firestore:rules
   ```

### Step 3: Build & Deploy Container to Cloud Run
```bash
# Build and deploy directly using Cloud Build & Cloud Run
gcloud run deploy student-result-portal \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GCP_PROJECT_ID=[YOUR_PROJECT_ID],ENV=production
```

---

## 🔒 Security Design Highlights

- **Principle of Least Privilege**: Firestore security rules and Flask middleware strictly gate reads and writes based on verified identity tokens.
- **Audit Logging**: All marks changes are logged to an immutable `audit_logs` collection.
- **Input Sanitization**: CSV uploads validate headers, data types, score boundaries (0-100), and limit file size and max rows.
- **No Client Secrets**: Zero sensitive credentials are exposed in the client-side JavaScript.
