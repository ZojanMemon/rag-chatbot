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
    # Check if we're in production mode
    is_production = st.secrets.get("PRODUCTION", False)
    
    # Initialize session state for user
    if "user" not in st.session_state:
        st.session_state.user = None
    
    # Check if already authenticated
    if st.session_state.user:
        return True, st.session_state.user
    
    if not is_production:
        # Development mode - auto-login with dummy user
        dummy_user = {
            "email": "guest@example.com",
            "uid": "guest-user",
            "display_name": "Guest User"
        }
        st.session_state.user = dummy_user
        return True, dummy_user
    
    # Add custom CSS
    st.markdown("""
        <style>
        /* Page background */
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        /* Card styling */
        div[data-testid="stForm"] {
            border: none;
            border-radius: 20px;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: rgba(255, 255, 255, 0.05);
            padding: 0.5rem;
            border-radius: 15px;
            margin-bottom: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 60px;
            padding: 0 2rem;
            font-size: 1.1rem;
            background: transparent;
            border: none;
            color: #a0aec0;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: #ffffff;
            background: rgba(255, 255, 255, 0.1);
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(45deg, #3498db, #2980b9) !important;
            color: #ffffff !important;
            border-radius: 10px;
        }
        
        /* Input field styling */
        div[data-baseweb="input"] {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            border: 2px solid rgba(255, 255, 255, 0.1) !important;
            margin: 1rem 0 !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
            min-height: 45px !important;
        }
        
        div[data-baseweb="input"]:focus-within {
            border-color: #3498db !important;
            box-shadow: 0 0 0 4px rgba(52, 152, 219, 0.2) !important;
            background: rgba(255, 255, 255, 0.1) !important;
        }
        
        /* Input text styling */
        .stTextInput input, .stTextInput textarea {
            color: #ffffff !important;
            font-size: 1.1rem !important;
            background: transparent !important;
            border: none !important;
            width: 100% !important;
            font-family: 'Inter', sans-serif !important;
            padding: 0.5rem 1rem !important;
            line-height: 1.5 !important;
            margin: 0 !important;
            height: auto !important;
            min-height: 45px !important;
        }
        
        .stTextInput input::placeholder, .stTextInput textarea::placeholder {
            color: rgba(255, 255, 255, 0.5) !important;
        }
        
        .stTextInput label {
            color: #a0aec0 !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            padding: 0.5rem 0 !important;
            margin-bottom: 0.25rem !important;
        }
        
        /* Button styling */
        .stButton button {
            width: 100%;
            height: 50px;
            background: linear-gradient(45deg, #3498db, #2980b9);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-top: 1.5rem;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }
        
        .stButton button:hover {
            background: linear-gradient(45deg, #2980b9, #3498db);
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(52, 152, 219, 0.3);
        }
        
        /* Message styling */
        .stAlert {
            background: rgba(255, 255, 255, 0.05) !important;
            border: none !important;
            border-radius: 12px !important;
            backdrop-filter: blur(10px);
            margin: 1rem 0 !important;
            padding: 1rem !important;
        }
        
        /* Heading styles */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif !important;
            letter-spacing: -0.5px !important;
        }
        
        /* Welcome text animation */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .welcome-text {
            animation: fadeIn 0.8s ease-out;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center the form with more space
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
            <div class="welcome-text">
                <h1 style='text-align: center; margin-bottom: 2rem; color: #3498db; font-size: 2.5rem; font-weight: 700;'>
                    Welcome Back! 👋
                </h1>
                <p style='text-align: center; color: #a0aec0; font-size: 1.1rem; margin-bottom: 2rem;'>
                    Log in to access your disaster management assistant
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for login and signup
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Sign Up"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=True):
                st.markdown("""
                    <h3 style='text-align: center; color: #e2e8f0; font-size: 1.5rem; margin-bottom: 2rem;'>
                        Login to Your Account
                    </h3>
                """, unsafe_allow_html=True)
                
                email = st.text_input(
                    "📧 Email Address",
                    key="login_email_input",
                    autocomplete="email"
                )
                password = st.text_input(
                    "🔒 Password",
                    type="password",
                    key="login_password_input",
                    autocomplete="current-password"
                )
                
                if st.form_submit_button("Login", type="primary", use_container_width=True):
                    if not email or not password:
                        st.error("Please fill in all fields")
                    else:
                        success, message = auth.login_form(email, password)
                        if message:
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        
        with tab2:
            with st.form("signup_form", clear_on_submit=True):
                st.markdown("""
                    <h3 style='text-align: center; color: #e2e8f0; font-size: 1.5rem; margin-bottom: 2rem;'>
                        Create New Account
                    </h3>
                """, unsafe_allow_html=True)
                
                email = st.text_input(
                    "📧 Email Address",
                    key="signup_email_input",
                    autocomplete="email"
                )
                password = st.text_input(
                    "🔒 Password",
                    type="password",
                    key="signup_password_input",
                    autocomplete="new-password"
                )
                confirm_password = st.text_input(
                    "🔒 Confirm Password",
                    type="password",
                    key="signup_confirm_input",
                    autocomplete="new-password"
                )
                
                if st.form_submit_button("Sign Up", type="primary", use_container_width=True):
                    if not email or not password or not confirm_password:
                        st.error("Please fill in all fields")
                    elif password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = auth.signup_form(email, password)
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
