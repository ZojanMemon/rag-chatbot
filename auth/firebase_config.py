"""
Firebase configuration for authentication and chat history storage.
This module handles the initialization of Firebase Admin SDK.
"""
import os
import json
import streamlit as st
from firebase_admin import credentials, initialize_app, firestore, auth, get_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_firebase():
    """
    Initialize Firebase Admin SDK with credentials.
    
    The function checks if Firebase is already initialized to prevent multiple initializations.
    It uses service account credentials stored in Streamlit secrets or environment variables.
    """
    try:
        # First check if app is already initialized
        try:
            app = get_app()
            if 'db' not in st.session_state:
                st.session_state.db = firestore.client()
            return True
        except ValueError:
            # App not initialized yet, proceed with initialization
            pass

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
            return False
        
        # Initialize the app with a name to prevent duplicate initialization
        firebase_app = initialize_app(cred, name='disaster-management-chatbot')
        st.session_state.db = firestore.client()
        return True
    except Exception as e:
        st.error(f"Error initializing Firebase: {str(e)}")
        return False

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
