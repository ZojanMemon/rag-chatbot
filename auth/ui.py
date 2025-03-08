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
            div.stButton > button {
                background-color: #252525 !important;
                border: none !important;
                color: #e0e0e0 !important;
                font-size: 0.9rem !important;
                text-align: left !important;
                min-height: unset !important;
                height: auto !important;
                line-height: 1.2 !important;
                margin: 0.25rem 0 !important;
                padding: 0.75rem !important;
                border-radius: 4px !important;
                transition: all 0.2s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                gap: 0.5rem !important;
            }
            
            div.stButton > button:hover {
                background-color: #353535 !important;
                transform: translateY(-1px);
            }
            
            div.stButton > button > div {
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                width: 100% !important;
            }
            
            .preview-text {
                flex: 1;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .delete-btn {
                opacity: 0.6;
                transition: opacity 0.2s;
                padding: 0.25rem;
                border-radius: 4px;
                margin-left: 0.5rem;
            }
            
            .delete-btn:hover {
                opacity: 1;
                background-color: #454545;
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
                
                # Create container for preview and delete button
                container = st.container()
                with container:
                    if st.button(
                        f'<div><span class="preview-text">{preview}</span><span class="delete-btn">🗑️</span></div>',
                        key=f"session_{session['id']}",
                        use_container_width=True,
                        help="Click to view conversation, click trash icon to delete"
                    ):
                        # Check if click was on delete icon area (right 20% of button)
                        if st.session_state.get('_last_clicked_pos_x', 0) > 0.8:
                            if history_manager.delete_session(user_id, session['id']):
                                if st.session_state.get('current_session_id') == session['id']:
                                    st.session_state.messages = []
                                    st.session_state.current_session_id = None
                                st.rerun()
                        else:
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
