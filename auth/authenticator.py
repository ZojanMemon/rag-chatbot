"""
Authentication module for user management.
Handles user registration, login, logout, and session management.
"""
import streamlit as st
import streamlit_authenticator as stauth
import bcrypt
import jwt
import datetime
from typing import Dict, Optional, Tuple, List
from firebase_admin import auth, firestore
from .firebase_config import get_firestore_db, initialize_firebase

class FirebaseAuthenticator:
    """
    Firebase-based authentication handler with Streamlit UI integration.
    
    This class manages user authentication using Firebase Authentication
    while providing a Streamlit-friendly interface.
    """
    
    def __init__(self):
        """Initialize the authenticator and ensure Firebase is set up."""
        initialize_firebase()
        self.db = get_firestore_db()
        
        # Initialize session state variables if they don't exist
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'authentication_status' not in st.session_state:
            st.session_state.authentication_status = None
        if 'username' not in st.session_state:
            st.session_state.username = None
    
    def login_form(self) -> Tuple[bool, str]:
        """
        Display login form and handle authentication.
        
        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        with st.form("login_form"):
            st.subheader("Login")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                return self._authenticate_user(email, password)
        
        return False, ""
    
    def signup_form(self) -> Tuple[bool, str]:
        """
        Display signup form and handle user registration.
        
        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        with st.form("signup_form"):
            st.subheader("Create an Account")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            password_confirm = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up")
            
            if submit:
                if password != password_confirm:
                    return False, "Passwords do not match"
                if not name or not email or not password:
                    return False, "All fields are required"
                
                return self._register_user(name, email, password)
        
        return False, ""
    
    def _authenticate_user(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        try:
            # Verify with Firebase Auth
            user = auth.get_user_by_email(email)
            
            # Get user from Firestore to check password
            user_doc = self.db.collection('users').document(user.uid).get()
            
            if not user_doc.exists:
                return False, "User not found"
            
            user_data = user_doc.to_dict()
            
            # Verify password
            if bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
                # Set session state
                st.session_state.user = {
                    'uid': user.uid,
                    'name': user_data.get('name', ''),
                    'email': email,
                    'preferences': user_data.get('preferences', {})
                }
                st.session_state.authentication_status = True
                st.session_state.username = user_data.get('name', '')
                
                return True, "Login successful"
            else:
                return False, "Incorrect password"
                
        except auth.UserNotFoundError:
            return False, "User not found"
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    def _register_user(self, name: str, email: str, password: str) -> Tuple[bool, str]:
        """
        Register a new user.
        
        Args:
            name: User's full name
            email: User's email
            password: User's password
            
        Returns:
            Tuple[bool, str]: (Success status, Message)
        """
        try:
            # Check if user already exists
            try:
                existing_user = auth.get_user_by_email(email)
                if existing_user:
                    return False, "Email already registered"
            except auth.UserNotFoundError:
                pass  # This is expected for new users
            
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Hash password for storage
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Store additional user data in Firestore
            self.db.collection('users').document(user.uid).set({
                'name': name,
                'email': email,
                'password_hash': password_hash,
                'created_at': firestore.SERVER_TIMESTAMP,
                'preferences': {
                    'input_language': 'English',
                    'output_language': 'English',
                    'theme': 'dark'
                }
            })
            
            # Automatically log in the user
            st.session_state.user = {
                'uid': user.uid,
                'name': name,
                'email': email,
                'preferences': {
                    'input_language': 'English',
                    'output_language': 'English',
                    'theme': 'dark'
                }
            }
            st.session_state.authentication_status = True
            st.session_state.username = name
            
            return True, "Account created successfully"
            
        except Exception as e:
            return False, f"Registration error: {str(e)}"
    
    def logout(self):
        """Log out the current user and clear session state."""
        st.session_state.user = None
        st.session_state.authentication_status = None
        st.session_state.username = None
    
    def is_authenticated(self) -> bool:
        """
        Check if a user is currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return st.session_state.authentication_status == True
    
    def get_current_user(self) -> Optional[Dict]:
        """
        Get the currently authenticated user.
        
        Returns:
            Optional[Dict]: User data or None if not authenticated
        """
        return st.session_state.user
    
    def update_user_preferences(self, preferences: Dict) -> bool:
        """
        Update user preferences in Firestore.
        
        Args:
            preferences: Dictionary of user preferences
            
        Returns:
            bool: Success status
        """
        if not self.is_authenticated():
            return False
        
        try:
            user_id = st.session_state.user['uid']
            
            # Update Firestore
            self.db.collection('users').document(user_id).update({
                'preferences': preferences
            })
            
            # Update session state
            st.session_state.user['preferences'] = preferences
            
            return True
        except Exception as e:
            st.error(f"Error updating preferences: {str(e)}")
            return False
