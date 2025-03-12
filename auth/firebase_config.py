"""
Firebase configuration and initialization.
"""
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json

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

def get_service_account_info():
    """Get the Firebase service account info from Streamlit secrets or environment."""
    try:
        # Try getting from Streamlit secrets first
        service_account_json = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
        return json.loads(service_account_json)
    except Exception as e:
        # Fall back to file-based approach
        service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
        if service_account_path:
            if os.path.isabs(service_account_path):
                path = service_account_path
            else:
                # Convert relative path to absolute
                path = str(Path(__file__).parent.parent / service_account_path)
        else:
            # Check current directory
            root_dir = Path(__file__).parent.parent
            path = root_dir / 'firebase-service-account.json'
            
        if not os.path.exists(path):
            raise ValueError(
                "Firebase service account not found. Please set FIREBASE_SERVICE_ACCOUNT "
                "in Streamlit secrets or provide a valid service account file."
            )
            
        with open(path) as f:
            return json.load(f)

def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    try:
        firebase_admin.get_app()
    except ValueError:
        # Not initialized, so initialize
        service_account_info = get_service_account_info()
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)

def get_firestore_db():
    """Get Firestore database client."""
    try:
        return firestore.client()
    except Exception:
        return None
