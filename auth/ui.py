"""
Authentication UI components for Streamlit.
Provides login, signup, and user profile management interfaces.
"""
import streamlit as st
from typing import Tuple, Optional, Dict, List, Callable
from .authenticator import FirebaseAuthenticator
from .chat_history import ChatHistoryManager
from datetime import datetime

def auth_page() -> Tuple[bool, Optional[Dict]]:
    """Handle user authentication and return authentication status."""
    
    # Check if user is already authenticated via session state
    if 'user_token' in st.session_state:
        try:
            user = auth.verify_id_token(st.session_state.user_token)
            return True, user
        except:
            # Token expired or invalid, clear it
            st.session_state.pop('user_token', None)
            st.session_state.pop('user', None)
    
    # Check for token in URL parameters
    if 'token' in st.query_params:
        try:
            user = auth.verify_id_token(st.query_params['token'])
            st.session_state.user_token = st.query_params['token']
            st.session_state.user = user
            # Remove token from URL
            st.query_params.clear()
            st.rerun()
            return True, user
        except:
            pass
    
    return False, None

def login_page():
    """Display the login page with authentication options."""
    st.markdown("""
        <style>
        .auth-container {
            max-width: 400px;
            margin: 100px auto;
            padding: 2rem;
            background: #1E1E1E;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .auth-title {
            text-align: center;
            margin-bottom: 2rem;
            color: #E0E0E0;
        }
        .auth-description {
            text-align: center;
            margin-bottom: 2rem;
            color: #808080;
            font-size: 0.9rem;
        }
        .auth-button {
            width: 100%;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            border: none;
            border-radius: 4px;
            background: #252525;
            color: #E0E0E0;
            font-size: 1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            transition: all 0.2s ease;
            text-decoration: none;
        }
        .auth-button:hover {
            background: #353535;
            transform: translateY(-1px);
        }
        .auth-button.email {
            background: #404040;
        }
        .auth-button.google {
            background: #4285F4;
        }
        .auth-button.github {
            background: #24292E;
        }
        .auth-features {
            margin-top: 2rem;
            padding: 1rem;
            background: #252525;
            border-radius: 4px;
        }
        .auth-features ul {
            margin: 0;
            padding-left: 1.5rem;
            color: #808080;
            font-size: 0.9rem;
        }
        .auth-features li {
            margin: 0.5rem 0;
        }
        </style>
        <div class="auth-container">
            <h1 class="auth-title">🚨 Disaster Management Assistant</h1>
            <p class="auth-description">Please sign in to continue using the chatbot</p>
            <a href="/auth/email" class="auth-button email">
                ✉️ Continue with Email
            </a>
            <a href="/auth/google" class="auth-button google">
                <img src="https://www.google.com/favicon.ico" width="20" height="20" style="border-radius: 50%">
                Continue with Google
            </a>
            <a href="/auth/github" class="auth-button github">
                <img src="https://github.com/favicon.ico" width="20" height="20" style="border-radius: 50%">
                Continue with GitHub
            </a>
            <div class="auth-features">
                <ul>
                    <li>Secure authentication via Firebase</li>
                    <li>Your chat history will be saved</li>
                    <li>Access from any device</li>
                    <li>Multi-language support</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)

def user_sidebar(user: Dict) -> None:
    """
    Display user information and options in the sidebar.
    
    Args:
        user: User data dictionary
    """
    auth = FirebaseAuthenticator()
    
    # User profile section with proper styling
    st.markdown(f"""
        <div style='background-color: white; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
            <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                <span style='font-size: 2rem;'>👤</span>
                <h3 style='margin: 0; color: #1a1a1a;'>User Profile</h3>
            </div>
            <div style='color: #4a4a4a;'>
                <p style='margin: 0.5rem 0;'><strong>Name:</strong> {user['name']}</p>
                <p style='margin: 0.5rem 0;'><strong>Email:</strong> {user['email']}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Sign out button
    if st.button("🚪 Sign Out", type="primary", use_container_width=True):
        auth.logout()
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
        # Clear any remaining session state
        st.session_state.messages = []
        st.session_state.current_session_id = None
        return
    
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
        # Skip empty sessions
        messages = history_manager.get_session_history(user_id, session['id'])
        if not messages:
            history_manager.delete_session(user_id, session['id'])
            continue
            
        # Get first message as preview (only first few words)
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
    preferences = user.get('preferences', {})
    
    # Set language preferences
    if 'input_language' in preferences:
        st.session_state.input_language = preferences['input_language']
    if 'output_language' in preferences:
        st.session_state.output_language = preferences['output_language']
    
    return preferences

def save_user_preferences(user_id: str) -> None:
    """
    Save current preferences to user profile.
    
    Args:
        user_id: User ID
    """
    auth = FirebaseAuthenticator()
    
    preferences = {
        'input_language': st.session_state.input_language,
        'output_language': st.session_state.output_language,
    }
    
    auth.update_user_preferences(preferences)
