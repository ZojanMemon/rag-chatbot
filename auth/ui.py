"""
Authentication UI components for Streamlit.
Provides login, signup, and user profile management interfaces.
"""
import streamlit as st
from typing import Tuple, Optional, Dict, List, Callable
from .authenticator import FirebaseAuthenticator
from .chat_history import ChatHistoryManager
from .firebase_config import get_firestore_db
from datetime import datetime
import json

def auth_page() -> Tuple[bool, Optional[Dict]]:
    """
    Display authentication page with login and signup options.
    
    Returns:
        Tuple[bool, Optional[Dict]]: (Authentication status, User data if authenticated)
    """
    auth = FirebaseAuthenticator()
    
    # Check if already authenticated
    if auth.is_authenticated():
        return True, auth.get_current_user()
    
    # Add custom CSS
    st.markdown("""
        <style>
        /* Modern form styling */
        div[data-testid="stForm"] {
            border: 1px solid #2c3e50;
            border-radius: 10px;
            padding: 20px;
            background: #1a1a1a;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #2c3e50;
            border-radius: 5px;
            color: #ffffff;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: #34495e;
            color: #ffffff;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #3498db !important;
            color: #ffffff !important;
        }
        
        /* Input field styling */
        div[data-baseweb="input"] {
            background: #2c3e50;
            border-radius: 5px;
            border: 1px solid #34495e;
            transition: all 0.3s ease;
        }
        
        div[data-baseweb="input"]:focus-within {
            border-color: #3498db;
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }
        
        /* Button styling */
        .stButton button {
            width: 100%;
            height: 45px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 5px;
            font-weight: 500;
            margin-top: 10px;
            transition: all 0.3s ease;
        }
        
        .stButton button:hover {
            background: linear-gradient(45deg, #2980b9, #3498db);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        
        /* Message styling */
        .stAlert {
            border-radius: 5px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-bottom: 30px; color: #3498db;'>Welcome Back! 👋</h1>", unsafe_allow_html=True)
        
        # Create tabs for login and signup
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                st.markdown("<h3 style='text-align: center; color: #bdc3c7;'>Login to Your Account</h3>", unsafe_allow_html=True)
                email = st.text_input("📧 Email Address", key="login_email")
                password = st.text_input("🔒 Password", type="password", key="login_password")
                
                if st.form_submit_button("Login", type="primary", use_container_width=True):
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        success, message = auth.login_form()
                        if message:
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        
        with tab2:
            with st.form("signup_form"):
                st.markdown("<h3 style='text-align: center; color: #bdc3c7;'>Create New Account</h3>", unsafe_allow_html=True)
                email = st.text_input("📧 Email Address", key="signup_email")
                password = st.text_input("🔒 Password", type="password", key="signup_password")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", key="signup_confirm")
                
                if st.form_submit_button("Sign Up", type="primary", use_container_width=True):
                    if not email or not password or not confirm_password:
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = auth.signup_form()
                        if message:
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    
    return False, None

def user_sidebar(user: Dict) -> None:
    """
    Display user information and options in the sidebar.
    
    Args:
        user: User data dictionary
    """
    st.markdown("""
        <div style='background-color: #252525; padding: 1rem; border-radius: 4px; margin-bottom: 1rem;'>
            <h3 style='margin: 0 0 1rem 0; font-size: 1.2rem;'>👤 User Profile</h3>
            <p style='margin: 0.5rem 0;'><strong>Name:</strong> {display_name}</p>
            <p style='margin: 0.5rem 0;'><strong>Email:</strong> {email}</p>
        </div>
    """.format(
        display_name=user.get('display_name', 'User'),
        email=user.get('email', '')
    ), unsafe_allow_html=True)
    
    # Logout button
    if st.button("🚪 Logout", use_container_width=True):
        FirebaseAuthenticator().logout()
        st.rerun()

def chat_history_sidebar(user_id: str, on_session_change: Callable = None) -> None:
    """
    Display chat history management in the sidebar.
    
    Args:
        user_id: User ID
        on_session_change: Callback function when session changes
    """
    history_manager = ChatHistoryManager()
    
    # List existing sessions
    sessions = history_manager.get_all_sessions(user_id)
    
    if not sessions:
        st.caption("No previous conversations")
    else:
        # Custom CSS for chat history items
        st.markdown("""
            <style>
            .chat-history-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                width: 100%;
                padding: 0.5rem;
                margin: 0.25rem 0;
                background-color: #252525;
                border-radius: 4px;
                transition: all 0.2s ease;
            }
            .chat-history-item:hover {
                background-color: #353535;
                transform: translateY(-1px);
            }
            .chat-preview {
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                margin-right: 0.5rem;
                font-size: 0.9rem;
            }
            .delete-button {
                flex-shrink: 0;
                opacity: 0.6;
                transition: opacity 0.2s;
                font-size: 0.9rem;
                padding: 0.25rem;
                border-radius: 4px;
            }
            .delete-button:hover {
                opacity: 1;
                background-color: #4d4d4d;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Sort sessions by creation time, newest first
        sessions = sorted(sessions, key=lambda x: x.get('created_at', 0), reverse=True)
        
        for session in sessions:
            # Get first message as preview
            messages = history_manager.get_session_history(user_id, session['id'])
            if messages:
                first_msg = messages[0]['content']
                words = first_msg.split()[:3]  # Get first 3 words
                preview = ' '.join(words) + '...'
                
                # Create a container for each chat session
                container = st.container()
                with container:
                    col1, col2 = st.columns([0.85, 0.15])
                    
                    with col1:
                        # Session button with preview
                        if st.button(
                            preview,
                            key=f"session_{session['id']}",
                            use_container_width=True
                        ):
                            history_manager._set_current_session_id(user_id, session['id'])
                            messages = history_manager.get_session_history(user_id, session['id'])
                            st.session_state.messages = [
                                {"role": msg["role"], "content": msg["content"]} 
                                for msg in messages
                            ]
                            st.session_state.current_session_id = session['id']
                            if on_session_change:
                                on_session_change(session['id'])
                            st.rerun()
                    
                    with col2:
                        # Delete button with tooltip
                        if st.button("🗑️", key=f"delete_{session['id']}", help="Delete conversation"):
                            if history_manager.delete_session(user_id, session['id']):
                                # If deleted current session, clear messages
                                if st.session_state.get('current_session_id') == session['id']:
                                    st.session_state.messages = []
                                    st.session_state.current_session_id = None
                                st.rerun()

def sync_chat_message(user_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> None:
    """
    Sync a chat message with Firebase.
    
    This function should be called whenever a new message is added to the chat.
    
    Args:
        user_id: User ID
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Additional message metadata
    """
    if not user_id:
        return
        
    history_manager = ChatHistoryManager()
    history_manager.save_message(user_id, role, content, metadata)

def load_user_preferences(user: Dict) -> Dict:
    """
    Load user preferences and apply them to the session state.
    
    Args:
        user: User data dictionary
        
    Returns:
        Dict: User preferences
    """
    if not user:
        return {
            'input_language': 'English',
            'output_language': 'English'
        }
    
    # Get Firestore client
    db = get_firestore_db()
    if not db:
        return {
            'input_language': 'English',
            'output_language': 'English'
        }
    
    try:
        # Get user preferences from Firestore
        user_doc = db.collection('users').document(user['uid']).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            preferences = user_data.get('preferences', {})
            
            # Set session state
            st.session_state.input_language = preferences.get('input_language', 'English')
            st.session_state.output_language = preferences.get('output_language', 'English')
            
            return preferences
    except Exception as e:
        st.error(f"Error loading preferences: {str(e)}")
    
    return {
        'input_language': 'English',
        'output_language': 'English'
    }

def save_user_preferences(user_id: str) -> None:
    """
    Save current preferences to user profile.
    
    Args:
        user_id: User ID
    """
    if not user_id:
        return
    
    # Get current preferences from session state
    preferences = {
        'input_language': st.session_state.get('input_language', 'English'),
        'output_language': st.session_state.get('output_language', 'English')
    }
    
    # Get Firestore client
    db = get_firestore_db()
    if not db:
        st.error("Could not connect to database")
        return
    
    try:
        # Update preferences in Firestore
        db.collection('users').document(user_id).update({
            'preferences': preferences
        })
        
        # Update session state
        st.session_state.user['preferences'] = preferences
        
        # Update cookie if using persistence
        if 'auth_cookie' in st.session_state:
            user_data = st.session_state.user
            st.session_state.auth_cookie = json.dumps(user_data)
            
    except Exception as e:
        st.error(f"Error saving preferences: {str(e)}")
