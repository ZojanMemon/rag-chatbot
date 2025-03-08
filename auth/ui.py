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
    
    # New chat button with icon
    if st.button("✨ Start New Chat", type="primary", use_container_width=True):
        session_id = history_manager.create_new_session(user_id)
        st.session_state.messages = []
        if on_session_change:
            on_session_change(session_id)
        st.rerun()
    
    # List existing sessions
    sessions = history_manager.get_all_sessions(user_id)
    
    if not sessions:
        st.caption("No previous conversations")
    else:
        # Custom CSS for chat history items
        st.markdown("""
            <style>
            .chat-history-item {
                background-color: white;
                border: 1px solid #e6e6e6;
                border-radius: 4px;
                padding: 0.75rem;
                margin: 0.5rem 0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                transition: all 0.3s ease;
            }
            .chat-history-item:hover {
                background-color: #f8f9fa;
                border-color: #d9d9d9;
            }
            .delete-button {
                opacity: 0.6;
                transition: opacity 0.3s ease;
            }
            .delete-button:hover {
                opacity: 1;
            }
            </style>
        """, unsafe_allow_html=True)
        
        for session in sessions:
            # Create a container for each chat session
            with st.container():
                col1, col2 = st.columns([0.9, 0.1])
                
                with col1:
                    # Get first message as preview
                    preview = "New Conversation"
                    messages = history_manager.get_session_history(user_id, session['id'])
                    if messages:
                        first_msg = messages[0]['content']
                        preview = (first_msg[:40] + '...') if len(first_msg) > 40 else first_msg
                    
                    # Session button with preview and icon
                    if st.button(
                        f"💭 {preview}",
                        key=f"session_{session['id']}",
                        use_container_width=True
                    ):
                        history_manager._set_current_session_id(user_id, session['id'])
                        messages = history_manager.get_session_history(user_id, session['id'])
                        st.session_state.messages = [
                            {"role": msg["role"], "content": msg["content"]} 
                            for msg in messages
                        ]
                        if on_session_change:
                            on_session_change(session['id'])
                        st.rerun()
                
                with col2:
                    # Delete button with tooltip
                    if st.button("🗑️", key=f"delete_{session['id']}", help="Delete conversation"):
                        if history_manager.delete_session(user_id, session['id']):
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
