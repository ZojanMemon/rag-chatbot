"""
Firebase configuration for authentication and chat history storage.
This module handles the initialization of Firebase Admin SDK.
"""
import os
import json
import streamlit as st
from firebase_admin import credentials, initialize_app, firestore, auth, get_app
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables
load_dotenv()

def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK with credentials.
    
    The function checks if Firebase is already initialized to prevent multiple initializations.
    It uses service account credentials stored in Streamlit secrets or environment variables.
    """
    if not get_app():
        # Get Firebase credentials
        if 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
            cred_dict = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            cred = credentials.Certificate(cred_dict)
        elif os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
            cred_dict = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
            cred = credentials.Certificate(cred_dict)
        elif os.path.exists('firebase-service-account.json'):
            cred = credentials.Certificate('firebase-service-account.json')
        else:
            st.error("Firebase credentials not found. Please set up Firebase credentials.")
            return
        
        # Initialize the app with a name to prevent duplicate initialization
        initialize_app(cred, name='disaster-management-chatbot')
        st.session_state.db = firestore.client()

def get_firestore_db():
    """
    Get the Firestore database client.
    
    Returns:
        Firestore client or None if not initialized
    """
    if 'db' in st.session_state:
        return st.session_state.db
    else:
        initialize_firebase()
        return st.session_state.db if 'db' in st.session_state else None

def get_auth_url(provider: str) -> str:
    """Get authentication URL for the specified provider."""
    base_url = st.secrets.get('AUTH_BASE_URL', 'http://localhost:8501')
    return f"{base_url}/auth/{provider}"

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token and return user info."""
    try:
        # Initialize Firebase if not already initialized
        initialize_firebase()
        # Verify the ID token
        return auth.verify_id_token(token)
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None
