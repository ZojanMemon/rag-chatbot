"""Context Manager for the Disaster Management Chatbot.

This module handles conversation context and memory to make the chatbot
aware of previous messages in the conversation.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

class ConversationContext:
    """Manages conversation context for the chatbot."""
    
    def __init__(self, max_context_length: int = 10):
        """Initialize the conversation context manager.
        
        Args:
            max_context_length: Maximum number of conversation turns to remember
        """
        self.max_context_length = max_context_length
        
        # Initialize context in session state if not present
        if "context_history" not in st.session_state:
            st.session_state.context_history = []
            
        # Initialize context summary in session state if not present
        if "context_summary" not in st.session_state:
            st.session_state.context_summary = ""
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a message to the conversation context.
        
        Args:
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
            metadata: Additional metadata for the message
        """
        # Create message object
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        # Add to context history
        st.session_state.context_history.append(message)
        
        # Trim context if it exceeds max length
        if len(st.session_state.context_history) > self.max_context_length:
            st.session_state.context_history = st.session_state.context_history[-self.max_context_length:]
        
        # Update context summary
        self._update_context_summary()
    
    def get_context_history(self) -> List[Dict[str, Any]]:
        """Get the conversation context history.
        
        Returns:
            List of message objects in the conversation history
        """
        return st.session_state.context_history
    
    def get_context_summary(self) -> str:
        """Get a summary of the conversation context.
        
        Returns:
            String summarizing the conversation context
        """
        return st.session_state.context_summary
    
    def get_formatted_context(self) -> str:
        """Get the conversation context formatted for the LLM.
        
        Returns:
            Formatted string containing the conversation context
        """
        formatted_context = "Previous conversation:\n"
        
        for message in st.session_state.context_history:
            role_prefix = "User: " if message["role"] == "user" else "Assistant: "
            formatted_context += f"{role_prefix}{message['content']}\n"
        
        return formatted_context
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        st.session_state.context_history = []
        st.session_state.context_summary = ""
    
    def _update_context_summary(self) -> None:
        """Update the context summary based on the conversation history."""
        # Simple implementation: just count messages
        user_messages = sum(1 for msg in st.session_state.context_history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in st.session_state.context_history if msg["role"] == "assistant")
        
        summary = f"Conversation with {user_messages} user messages and {assistant_messages} assistant responses."
        
        # Extract key topics if available
        topics = set()
        for msg in st.session_state.context_history:
            # Look for emergency keywords in user messages
            if msg["role"] == "user":
                content_lower = msg["content"].lower()
                emergency_keywords = ["flood", "earthquake", "fire", "medical", "emergency", "help"]
                for keyword in emergency_keywords:
                    if keyword in content_lower:
                        topics.add(keyword)
        
        if topics:
            topic_str = ", ".join(topics)
            summary += f" Topics discussed: {topic_str}."
        
        st.session_state.context_summary = summary

    def get_context_for_rag(self, current_query: str) -> str:
        """Get the conversation context formatted for RAG system.
        
        This formats the context in a way that can be included in the RAG query
        to provide conversation history to the model.
        
        Args:
            current_query: The current user query
            
        Returns:
            Formatted string containing relevant context for the RAG system
        """
        # Get the last few turns of conversation (most relevant)
        recent_context = st.session_state.context_history[-min(5, len(st.session_state.context_history)):]
        
        # Format the context for the RAG system
        context_for_rag = "Consider this conversation history when answering:\n"
        
        for message in recent_context:
            role_prefix = "User: " if message["role"] == "user" else "Assistant: "
            context_for_rag += f"{role_prefix}{message['content']}\n"
        
        context_for_rag += f"\nCurrent question: {current_query}\n"
        
        return context_for_rag
