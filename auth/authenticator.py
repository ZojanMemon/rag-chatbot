"""
Firebase authentication handler for Streamlit.
"""
import streamlit as st
from firebase_admin import auth
from .firebase_config import get_firestore_db, initialize_firebase
import json
import base64

class FirebaseAuthenticator:
    """Firebase authentication handler."""
    
    def __init__(self):
        """Initialize the authenticator."""
        # Ensure Firebase is initialized
        initialize_firebase()
        self.db = get_firestore_db()
        
        # Initialize session state for auth
        if 'user' not in st.session_state:
            # Try to load user from URL params first
            params = st.experimental_get_query_params()
            if 'auth_token' in params:
                try:
                    auth_token = base64.b64decode(params['auth_token'][0]).decode('utf-8')
                    user_data = json.loads(auth_token)
                    st.session_state.user = user_data
                except:
                    st.session_state.user = None
            else:
                st.session_state.user = None
    
    def _save_auth_token(self, user_data: dict):
        """Save auth token to URL params."""
        auth_token = base64.b64encode(json.dumps(user_data).encode('utf-8')).decode('utf-8')
        st.experimental_set_query_params(auth_token=auth_token)
    
    def login_form(self):
        """Display login form and handle login."""
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", key="login_button"):
            if not email or not password:
                return False, "Please fill in all fields"
            
            try:
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
            except Exception as e:
                return False, f"Login failed: {str(e)}"
        
        return False, None
    
    def signup_form(self):
        """Display signup form and handle registration."""
        st.subheader("Create Account")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        if st.button("Sign Up", type="primary", key="signup_button"):
            if not email or not password or not confirm_password:
                return False, "Please fill in all fields"
            
            if password != confirm_password:
                return False, "Passwords do not match"
            
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
        
        return False, None
    
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
        st.experimental_set_query_params()
        # Clear other session state
        for key in ['messages', 'current_session_id']:
            if key in st.session_state:
                del st.session_state[key]
