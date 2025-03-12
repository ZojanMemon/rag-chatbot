"""
Firebase configuration and initialization.
"""
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

def get_firebase_api_key():
    """Get Firebase API key from environment variables or Streamlit secrets."""
    # Try getting from Streamlit secrets first
    try:
        return st.secrets["FIREBASE_API_KEY"]
    except:
        # Fall back to environment variable
        api_key = os.environ.get('FIREBASE_API_KEY')
        if not api_key:
            raise ValueError(
                "Firebase API key not found. Please set it in Streamlit secrets or "
                "as an environment variable 'FIREBASE_API_KEY'."
            )
        return api_key

def get_service_account_path():
    """Get the path to the Firebase service account file."""
    # First try getting from Streamlit secrets
    try:
        import json
        service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
        
        # Write to a temporary file
        root_dir = Path(__file__).parent.parent
        temp_path = root_dir / 'firebase-service-account.json'
        with open(temp_path, 'w') as f:
            json.dump(service_account_json, f)
        return str(temp_path)
    except Exception:
        pass
        
    # Then check environment variable
    service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
    if service_account_path:
        if os.path.isabs(service_account_path):
            return service_account_path
        else:
            # Convert relative path to absolute
            return str(Path(__file__).parent.parent / service_account_path)
        
    # Then check current directory
    root_dir = Path(__file__).parent.parent
    service_account_path = root_dir / 'firebase-service-account.json'
    if service_account_path.exists():
        return str(service_account_path)
        
    # If no auth is found, create a dummy service account for development
    if not st.secrets.get("PRODUCTION", False):
        dummy_account = {
            "type": "service_account",
            "project_id": "dummy-project",
            "private_key_id": "dummy",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC9QFbDLHsGjwKR\n-----END PRIVATE KEY-----\n",
            "client_email": "dummy@dummy-project.iam.gserviceaccount.com",
            "client_id": "dummy",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "dummy"
        }
        with open(service_account_path, 'w') as f:
            json.dump(dummy_account, f)
        return str(service_account_path)
        
    raise ValueError(
        "Firebase service account not found. Please set it in Streamlit secrets as FIREBASE_SERVICE_ACCOUNT, "
        "in environment variable FIREBASE_SERVICE_ACCOUNT_PATH, or place firebase-service-account.json in the project root."
    )

def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    try:
        firebase_admin.get_app()
    except ValueError:
        # Not initialized, so initialize
        service_account_path = get_service_account_path()
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)

def get_firestore_db():
    """Get Firestore database client."""
    try:
        return firestore.client()
    except Exception:
        return None
