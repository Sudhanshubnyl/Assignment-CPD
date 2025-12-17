EV FastAPI + Firebase Auth + Firestore on Cloud Run (CI/CD with Cloud Build)
1) Project Overview

This project is a FastAPI web application that works as a simple Electric Vehicle (EV) database. Users can sign up and log in using Firebase Authentication, then browse EV records stored in Firestore, search/filter records, add new EVs (authenticated users only), compare two EVs, and submit reviews. The application uses Jinja2 templates for the UI and serves static assets (CSS + Firebase login JS) from a /static directory.

The goal of the deployment was to run the app on Google Cloud using a production-ready approach: containerised deployment on Cloud Run, secure secret storage using Secret Manager, Firestore as the database, and automated builds/deployments using Cloud Build triggers.

2) Core Features (What the app can do)

Firebase Authentication (Signup / Login / Logout)

Token is stored in browser cookies and verified by backend for protected actions

EV listing (homepage shows EV cards from Firestore)
Search/filter EVs by model/manufacturer/cost/range
Add a new EV (only for authenticated users)
View detailed EV information page (including average rating)
Submit EV reviews (stored in a reviews subcollection per EV document)
Compare two EVs side-by-side (ratings + key fields)

3) Tech Stack

Backend
FastAPI
Uvicorn (ASGI server)
Jinja2 templates
Firebase Admin SDK (server-side token verification)
Google Cloud Firestore client
Frontend
Jinja2 HTML templates
CSS (static/styles.css)
Firebase Web SDK (static/firebase-login.js) for login/signup

Cloud

Cloud Run (compute / container runtime)
Cloud Build (CI/CD)
Artifact Registry (store built container images)
Secret Manager (store Firebase service-account JSON)
Firestore (database)

4) Repository Structure

Project root contains:

main.py → FastAPI app entrypoint, routes, auth validation, template rendering
query.py → Firestore helper functions (fetch, update, reviews, etc.)
templates/ → UI templates (main.html, add_vehicles.html, etc.)
static/ → frontend assets (styles.css, firebase-login.js)
requirements.txt → Python dependencies
Dockerfile → container build recipe
cloudbuild.yaml → CI/CD pipeline definition (build → push → deploy)

5) Local Setup (Run on your laptop)
Prerequisites

Python 3.11+
A Firebase project with Authentication enabled
A Firestore database
Firebase Admin service account JSON

Steps
Create and activate a virtual environment

Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

Mac/Linux:
python3 -m venv .venv
source .venv/bin/activate

Install dependencies
pip install -r requirements.txt

Set environment variables
You must point to the Firebase Admin JSON credentials file.

Windows (PowerShell)
$env:FIREBASE_CREDENTIALS_PATH="C:\path\to\firebase-admin.json"

Mac/Linux
export FIREBASE_CREDENTIALS_PATH="/path/to/firebase-admin.json"

Optional (if using a Firestore Native database name):
export FIRESTORE_DATABASE="assignment"

Run the application
uvicorn main:app --host 0.0.0.0 --port 8000

Open in browser
http://localhost:8000

6) Cloud Deployment Overview (What happens in GCP)

In cloud deployment, we containerise the app and run it on Cloud Run. Secrets are not stored in GitHub or in the container image. Instead:

Firebase Admin JSON is stored in Secret Manager (FIREBASE_SA_JSON)
Cloud Run mounts it at /secrets/firebase-sa.json
App reads it using: FIREBASE_CREDENTIALS_PATH=/secrets/firebase-sa.json
Firestore database is targeted using: FIRESTORE_DATABASE=assignment

7) Secret Manager (Firebase Admin JSON)
Create secret (run in Cloud Shell)

Upload the JSON into Cloud Shell first, then:
gcloud secrets create FIREBASE_SA_JSON --data-file="your-firebase-admin.json"

Verify:
gcloud secrets describe FIREBASE_SA_JSON

8) IAM Roles Required (High-level)

To make the CI/CD pipeline fully automated:
Cloud Build service account needs
permission to deploy Cloud Run (roles/run.admin)
permission to act as runtime service account (roles/iam.serviceAccountUser)
Cloud Run runtime service account needs
Secret Manager access (roles/secretmanager.secretAccessor)
Firestore access (commonly roles/datastore.user for Firestore access patterns)

9) CI/CD Pipeline (Cloud Build Trigger)

We created a Cloud Build trigger connected to GitHub so that every push triggers:
Build Docker image
Push image to Artifact Registry
Deploy latest image to Cloud Run with correct env vars + secret mount
This ensures deployments are repeatable and consistent.

10) cloudbuild.yaml Explanation (What each step does)
Substitutions

Defines reusable variables like region, service name, repository, runtime service account.
Step 1: Build
Builds Docker image from the repo and tags it with a unique $BUILD_ID.
Step 2: Push
Pushes the image to Artifact Registry so Cloud Run can pull it later.
Step 3: Deploy
Deploys the pushed image to Cloud Run, attaches:
runtime service account
secret file mount for Firebase JSON
env vars for Firestore DB and credentials path

Logging

Sends Cloud Build logs to Cloud Logging only (helps avoid logs bucket issues and makes debugging easier).

11) Common Issues and Fixes (What i solved)

“Mixed Content blocked” → ensure assets load via HTTPS and cookie flags are correct
Firestore 403 / wrong project → enable Firestore API in correct project and set FIRESTORE_DATABASE correctly
Container fails to start → usually caused by import/runtime errors (missing module, missing os import, etc.)
GitHub push failing → GitHub removed password auth; use token-based auth
Trigger failing due to logging config → resolved by using logging: CLOUD_LOGGING_ONLY


