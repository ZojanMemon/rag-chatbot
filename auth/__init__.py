"""
Authentication and chat history management package.
"""
from .authenticator import FirebaseAuthenticator
from .chat_history import ChatHistoryManager
from .firebase_config import initialize_firebase, get_firestore_db

__all__ = [
    'FirebaseAuthenticator',
    'ChatHistoryManager',
    'initialize_firebase',
    'get_firestore_db'
]
