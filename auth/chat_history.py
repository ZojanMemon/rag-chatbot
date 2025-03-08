"""
Chat history management module.
Handles storing, retrieving, and managing user chat histories in Firebase.
"""
import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
from firebase_admin import firestore
from .firebase_config import get_firestore_db

class ChatHistoryManager:
    """
    Manages chat history storage and retrieval from Firebase Firestore.
    
    This class handles saving chat messages, retrieving conversation history,
    and managing chat sessions for authenticated users.
    """
    
    def __init__(self):
        """Initialize the chat history manager with Firestore database."""
        self.db = get_firestore_db()
    
    def save_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Save a chat message to Firestore.
        
        Args:
            user_id: The user's ID
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Additional message metadata (language, etc.)
            
        Returns:
            bool: Success status
        """
        if not self.db:
            return False
            
        try:
            # Get or create a chat session
            session_id = self._get_current_session_id(user_id)
            
            # Create message document
            message_data = {
                'role': role,
                'content': content,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'metadata': metadata or {}
            }
            
            # Add to messages collection
            self.db.collection('users').document(user_id) \
                .collection('chat_sessions').document(session_id) \
                .collection('messages').add(message_data)
                
            return True
        except Exception as e:
            st.error(f"Error saving message: {str(e)}")
            return False
    
    def get_session_history(self, user_id: str, session_id: Optional[str] = None) -> List[Dict]:
        """
        Retrieve chat history for a specific session.
        
        Args:
            user_id: The user's ID
            session_id: Optional session ID (uses current session if None)
            
        Returns:
            List[Dict]: List of message documents
        """
        if not self.db:
            return []
            
        try:
            # Get session ID (current or specified)
            if not session_id:
                session_id = self._get_current_session_id(user_id)
            
            # Query messages
            messages_ref = self.db.collection('users').document(user_id) \
                .collection('chat_sessions').document(session_id) \
                .collection('messages').order_by('timestamp')
                
            # Get messages
            messages = []
            for doc in messages_ref.stream():
                message = doc.to_dict()
                message['id'] = doc.id
                messages.append(message)
                
            return messages
        except Exception as e:
            st.error(f"Error retrieving chat history: {str(e)}")
            return []
    
    def get_all_sessions(self, user_id: str) -> List[Dict]:
        """
        Get all chat sessions for a user.
        
        Args:
            user_id: The user's ID
            
        Returns:
            List[Dict]: List of session documents
        """
        if not self.db:
            return []
            
        try:
            # Query sessions
            sessions_ref = self.db.collection('users').document(user_id) \
                .collection('chat_sessions').order_by('created_at', direction=firestore.Query.DESCENDING)
                
            # Get sessions
            sessions = []
            for doc in sessions_ref.stream():
                session = doc.to_dict()
                session['id'] = doc.id
                sessions.append(session)
                
            return sessions
        except Exception as e:
            st.error(f"Error retrieving sessions: {str(e)}")
            return []
    
    def create_new_session(self, user_id: str, title: str = "New Chat") -> str:
        """
        Create a new chat session.
        
        Args:
            user_id: The user's ID
            title: Session title
            
        Returns:
            str: New session ID
        """
        if not self.db:
            return ""
            
        try:
            # Create session document
            session_data = {
                'title': title,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add to sessions collection
            session_ref = self.db.collection('users').document(user_id) \
                .collection('chat_sessions').add(session_data)
                
            session_id = session_ref[1].id
            
            # Set as current session
            self._set_current_session_id(user_id, session_id)
            
            return session_id
        except Exception as e:
            st.error(f"Error creating session: {str(e)}")
            return ""
    
    def delete_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            user_id: The user's ID
            session_id: Session ID to delete
            
        Returns:
            bool: Success status
        """
        if not self.db:
            return False
            
        try:
            # Delete all messages in the session
            messages_ref = self.db.collection('users').document(user_id) \
                .collection('chat_sessions').document(session_id) \
                .collection('messages')
                
            self._delete_collection(messages_ref, 100)
            
            # Delete the session document
            self.db.collection('users').document(user_id) \
                .collection('chat_sessions').document(session_id).delete()
                
            # If this was the current session, create a new one
            if self._get_current_session_id(user_id) == session_id:
                self.create_new_session(user_id)
                
            return True
        except Exception as e:
            st.error(f"Error deleting session: {str(e)}")
            return False
    
    def update_session_title(self, user_id: str, session_id: str, title: str) -> bool:
        """
        Update a chat session's title.
        
        Args:
            user_id: The user's ID
            session_id: Session ID
            title: New title
            
        Returns:
            bool: Success status
        """
        if not self.db:
            return False
            
        try:
            # Update session document
            self.db.collection('users').document(user_id) \
                .collection('chat_sessions').document(session_id) \
                .update({
                    'title': title,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                
            return True
        except Exception as e:
            st.error(f"Error updating session title: {str(e)}")
            return False
    
    def _get_current_session_id(self, user_id: str) -> str:
        """
        Get the current session ID or create a new one.
        
        Args:
            user_id: The user's ID
            
        Returns:
            str: Session ID
        """
        # Check session state first
        if 'current_session_id' in st.session_state:
            return st.session_state.current_session_id
            
        try:
            # Check user preferences in Firestore
            user_doc = self.db.collection('users').document(user_id).get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                if 'current_session_id' in user_data:
                    session_id = user_data['current_session_id']
                    
                    # Verify session exists
                    session_doc = self.db.collection('users').document(user_id) \
                        .collection('chat_sessions').document(session_id).get()
                        
                    if session_doc.exists:
                        # Store in session state
                        st.session_state.current_session_id = session_id
                        return session_id
            
            # Create new session if none exists
            return self.create_new_session(user_id)
        except Exception as e:
            st.error(f"Error getting current session: {str(e)}")
            # Create new session as fallback
            return self.create_new_session(user_id)
    
    def _set_current_session_id(self, user_id: str, session_id: str) -> None:
        """
        Set the current session ID.
        
        Args:
            user_id: The user's ID
            session_id: Session ID
        """
        # Update session state
        st.session_state.current_session_id = session_id
        
        try:
            # Update user document in Firestore
            self.db.collection('users').document(user_id).update({
                'current_session_id': session_id
            })
        except Exception as e:
            st.error(f"Error setting current session: {str(e)}")
    
    def _delete_collection(self, collection_ref, batch_size):
        """
        Helper method to delete a collection in batches.
        
        Args:
            collection_ref: Collection reference
            batch_size: Number of documents to delete in each batch
        """
        docs = collection_ref.limit(batch_size).stream()
        deleted = 0
        
        for doc in docs:
            doc.reference.delete()
            deleted += 1
            
        if deleted >= batch_size:
            # Recursive call to delete more documents
            self._delete_collection(collection_ref, batch_size)
