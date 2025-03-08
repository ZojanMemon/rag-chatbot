"""
Firebase configuration and initialization.
"""
import os
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_firebase_api_key():
    """Get Firebase API key from environment variables."""
    api_key = os.getenv('FIREBASE_API_KEY')
    if not api_key:
        raise ValueError("FIREBASE_API_KEY environment variable is not set")
    return api_key

def get_service_account_path():
    """Get the path to the Firebase service account file."""
    # First check environment variable
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    if service_account_path:
        return service_account_path
        
    # Then check current directory
    current_dir = Path(__file__).parent.parent
    service_account_path = current_dir / 'firebase-service-account.json'
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
