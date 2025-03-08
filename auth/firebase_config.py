"""
Firebase configuration for authentication and chat history storage.
This module handles the initialization of Firebase Admin SDK.
"""
import os
import json
import streamlit as st
from firebase_admin import credentials, initialize_app, firestore, auth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with credentials.
    
    The function checks if Firebase is already initialized to prevent multiple initializations.
    It uses service account credentials stored in Streamlit secrets or environment variables.
    """
    if not 'firebase_initialized' in st.session_state:
        try:
            # First, try to get credentials from Streamlit secrets
            if 'FIREBASE_SERVICE_ACCOUNT' in st.secrets:
                cred_dict = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                cred = credentials.Certificate(cred_dict)
            # If not in secrets, try to get from environment variable
            elif os.environ.get('FIREBASE_SERVICE_ACCOUNT'):
                cred_dict = json.loads(os.environ.get('FIREBASE_SERVICE_ACCOUNT'))
                cred = credentials.Certificate(cred_dict)
            # If not in environment, look for a service account file
            elif os.path.exists('firebase-service-account.json'):
                cred = credentials.Certificate('firebase-service-account.json')
            else:
                st.error("Firebase credentials not found. Please set up Firebase credentials.")
                return False
            
            # Initialize the app
            firebase_app = initialize_app(cred)
            st.session_state.firebase_initialized = True
            st.session_state.db = firestore.client()
            return True
        except Exception as e:
            st.error(f"Error initializing Firebase: {str(e)}")
            return False
    return True

def get_firestore_db():
    """
    Get the Firestore database client.
    
    Returns:
        Firestore client or None if not initialized
    """
    if 'db' in st.session_state:
        return st.session_state.db
    else:
        if initialize_firebase():
            return st.session_state.db
    return None
