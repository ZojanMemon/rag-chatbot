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
    """
    Display authentication page with login and signup options.
    
    Returns:
        Tuple[bool, Optional[Dict]]: (Authentication status, User data if authenticated)
    """
    auth = FirebaseAuthenticator()
    
    # Check if already authenticated
    if auth.is_authenticated():
        return True, auth.get_current_user()
    
    # Create tabs for login and signup
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        success, message = auth.login_form()
        if message:
            if success:
                st.success(message)
                st.rerun()  # Refresh the page after successful login
            else:
                st.error(message)
    
    with tab2:
        success, message = auth.signup_form()
        if message:
            if success:
                st.success(message)
                st.rerun()  # Refresh the page after successful signup
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
