"""RAG integration with conversation context.

This module provides utilities to integrate conversation context
with the existing RAG (Retrieval Augmented Generation) system.
"""
import streamlit as st
from typing import Dict, Any, Tuple, List, Optional
from .context_manager import ConversationContext

class ContextualRAG:
    """Integrates conversation context with RAG system."""
    
    def __init__(self, max_context_messages: int = 5):
        """Initialize the contextual RAG system.
        
        Args:
            max_context_messages: Maximum number of previous messages to include in context
        """
        self.context_manager = ConversationContext(max_context_messages=max_context_messages)
    
    def get_contextual_response(self, qa_chain: Any, query: str, messages: List[Dict[str, str]], 
                               lang_instruction: str = "") -> str:
        """Get a response from the RAG system with conversation context.
        
        Args:
            qa_chain: The initialized QA chain
            query: User's question
            messages: List of previous conversation messages
            lang_instruction: Language-specific instructions
            
        Returns:
            str: Generated response with context awareness
        """
        # Enhance query with conversation context
        contextual_query = self.context_manager.get_query_with_context(query, messages)
        
        # Add language instruction if provided
        if lang_instruction:
            contextual_query = f"{contextual_query}\n\n{lang_instruction}"
        
        # Get response from RAG system
        try:
            # Use a higher temperature for more contextual responses
            response = qa_chain({"query": contextual_query})
            
            # Debug logging (can be removed in production)
            if "debug_context" in st.session_state and st.session_state.debug_context:
                st.session_state.last_contextual_query = contextual_query
                
            return response['result']
        except Exception as e:
            return f"I'm sorry, I couldn't generate a response with context. Error: {str(e)}"
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        self.context_manager.clear_context()
