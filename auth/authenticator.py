"""
Firebase authentication handler for Streamlit.
"""
import streamlit as st
from firebase_admin import auth
from firebase_admin._auth_utils import InvalidIdTokenError
import requests
from .firebase_config import get_firestore_db, initialize_firebase, get_firebase_api_key
import json
import base64

class FirebaseAuthenticator:
    """Firebase authentication handler."""
    
    def __init__(self):
        """Initialize the authenticator."""
        # Ensure Firebase is initialized
        initialize_firebase()
        self.db = get_firestore_db()
        self.api_key = get_firebase_api_key()
        
        # Initialize session state for auth
        if 'user' not in st.session_state:
            # Try to load user from URL params first
            if 'auth_token' in st.query_params:
                try:
                    auth_token = base64.b64decode(st.query_params['auth_token']).decode('utf-8')
                    user_data = json.loads(auth_token)
                    st.session_state.user = user_data
                except:
                    st.session_state.user = None
            else:
                st.session_state.user = None
    
    def _save_auth_token(self, user_data: dict):
        """Save auth token to URL params."""
        auth_token = base64.b64encode(json.dumps(user_data).encode('utf-8')).decode('utf-8')
        st.query_params['auth_token'] = auth_token
    
    def login_form(self, email: str, password: str):
        """Handle login form submission."""
        try:
            # Get Firebase Auth REST API endpoint
            response = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}",
                json={
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }
            )
            
            if response.status_code != 200:
                error_message = response.json().get('error', {}).get('message', 'Login failed')
                if error_message == 'INVALID_PASSWORD':
                    return False, "Incorrect password"
                elif error_message == 'EMAIL_NOT_FOUND':
                    return False, "Email not found"
                else:
                    return False, f"Login failed: {error_message}"
            
            # Get user from Firebase Auth
            user = auth.get_user_by_email(email)
            
            # Store user data in session
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name or email.split('@')[0]
            }
            st.session_state.user = user_data
            
            # Save auth token to URL
            self._save_auth_token(user_data)
            
            # Initialize user document in Firestore if it doesn't exist
            if self.db:
                user_ref = self.db.collection('users').document(user.uid)
                if not user_ref.get().exists:
                    user_ref.set({
                        'email': user.email,
                        'display_name': user.display_name or email.split('@')[0],
                        'created_at': st.session_state.get('server_time', 0),
                        'preferences': {
                            'input_language': 'English',
                            'output_language': 'English'
                        }
                    })
            
            return True, "Login successful!"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Login failed: {str(e)}"
    
    def signup_form(self, email: str, password: str):
        """Handle signup form submission."""
        try:
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password
            )
            
            # Store user data in session
            user_data = {
                'uid': user.uid,
                'email': user.email,
                'display_name': email.split('@')[0]
            }
            st.session_state.user = user_data
            
            # Save auth token to URL
            self._save_auth_token(user_data)
            
            # Create user document in Firestore
            if self.db:
                self.db.collection('users').document(user.uid).set({
                    'email': user.email,
                    'display_name': email.split('@')[0],
                    'created_at': st.session_state.get('server_time', 0),
                    'preferences': {
                        'input_language': 'English',
                        'output_language': 'English'
                    }
                })
            
            return True, "Account created successfully!"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def is_authenticated(self):
        """Check if user is authenticated."""
        return st.session_state.user is not None
    
    def get_current_user(self):
        """Get current user data."""
        return st.session_state.user
    
    def logout(self):
        """Log out current user."""
        st.session_state.user = None
        # Clear URL params
        st.query_params.clear()
        # Clear other session state
        for key in ['messages', 'current_session_id']:
            if key in st.session_state:
                del st.session_state[key]
