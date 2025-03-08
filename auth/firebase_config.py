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
    # First check environment variable
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
        
    raise ValueError(
        "Firebase service account file not found. Please set FIREBASE_SERVICE_ACCOUNT_PATH "
        "environment variable or place firebase-service-account.json in the project root."
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
