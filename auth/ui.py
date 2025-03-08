"""
Authentication UI components for Streamlit.
Provides login, signup, and user profile management interfaces.
"""
import streamlit as st
from typing import Tuple, Optional, Dict, List, Callable
from .authenticator import FirebaseAuthenticator
from .chat_history import ChatHistoryManager

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
    
    with st.sidebar:
        st.write(f"👤 **{user['name']}**")
        st.write(f"📧 {user['email']}")
        
        if st.button("Logout"):
            auth.logout()
            st.rerun()  # Refresh the page after logout

def chat_history_sidebar(user_id: str, on_session_change: Callable = None) -> None:
    """
    Display chat history management in the sidebar.
    
    Args:
        user_id: User ID
        on_session_change: Callback function when session changes
    """
    history_manager = ChatHistoryManager()
    
    with st.sidebar:
        st.subheader("💬 Chat History")
        
        # New chat button
        if st.button("➕ New Chat"):
            session_id = history_manager.create_new_session(user_id)
            st.session_state.messages = []  # Clear current messages
            if on_session_change:
                on_session_change(session_id)
            st.rerun()
        
        # List existing sessions
        sessions = history_manager.get_all_sessions(user_id)
        
        if not sessions:
            st.info("No chat history found")
        else:
            st.write("Recent Conversations:")
            
            for session in sessions:
                col1, col2 = st.columns([0.8, 0.2])
                
                with col1:
                    # Session title with click handler
                    if st.button(session['title'], key=f"session_{session['id']}"):
                        # Set as current session
                        history_manager._set_current_session_id(user_id, session['id'])
                        
                        # Load messages from this session
                        messages = history_manager.get_session_history(user_id, session['id'])
                        st.session_state.messages = [
                            {"role": msg["role"], "content": msg["content"]} 
                            for msg in messages
                        ]
                        
                        if on_session_change:
                            on_session_change(session['id'])
                        
                        st.rerun()
                
                with col2:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{session['id']}"):
                        if history_manager.delete_session(user_id, session['id']):
                            st.success("Session deleted")
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
        'theme': 'dark'  # Or get from session state if you track theme
    }
    
    auth.update_user_preferences(preferences)
