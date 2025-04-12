"""Integration utilities for the conversation context system.

This module provides simple functions to integrate the context-aware
functionality with the existing chatbot application.
"""
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
from .rag_context import ContextualRAG
from .context_manager import ConversationContext

# Initialize the contextual RAG system
contextual_rag = ContextualRAG(max_context_messages=5)

def get_contextual_rag_response(qa_chain: Any, query: str, lang_instruction: str = "") -> str:
    """
    Get a response from the RAG system with conversation context.
    
    This is a drop-in replacement for the existing get_rag_response function
    that adds conversation context awareness.
    
    Args:
        qa_chain: The initialized QA chain
        query: User's question
        lang_instruction: Language-specific instructions
        
    Returns:
        str: Generated response with context awareness
    """
    # Get messages from session state
    messages = st.session_state.get("messages", [])
    
    # Use the contextual RAG system to get a response
    return contextual_rag.get_contextual_response(qa_chain, query, messages, lang_instruction)

def get_contextual_response_with_language(qa_chain: Any, query: str):
    """
    Get a response from the RAG system with conversation context and language instruction.
    
    This function is designed to be a direct replacement for the existing get_rag_response
    function in app.py, maintaining compatibility with the language instruction handling.
    
    Args:
        qa_chain: The initialized QA chain
        query: User's question
        
    Returns:
        str: Generated response with context awareness and language instruction
    """
    try:
        # Import the language prompt function from the main app
        # We import here to avoid circular imports
        from app import get_language_prompt
        
        # Add language-specific instructions based on output language
        lang_instruction = get_language_prompt(st.session_state.output_language)
        
        # Check if context is enabled
        if st.session_state.get("context_enabled", True):
            # Get response with context
            return get_contextual_rag_response(qa_chain, query, lang_instruction)
        else:
            # Use the original RAG response without context
            from app import get_rag_response
            return get_rag_response(qa_chain, query)
    except Exception as e:
        st.error(f"Error generating contextual response: {str(e)}")
        return f"I'm sorry, I couldn't generate a response. Error: {str(e)}"

def clear_conversation_context() -> None:
    """
    Clear the conversation context.
    
    This should be called when starting a new conversation.
    """
    contextual_rag.clear_context()

def initialize_context_system() -> None:
    """
    Initialize the context system.
    
    This should be called during app initialization.
    """
    # Initialize context-related session state variables if needed
    if "context_enabled" not in st.session_state:
        st.session_state.context_enabled = True
