"""Conversation context management for the chatbot.

This module provides functionality to maintain and use conversation context
between user messages, allowing the chatbot to have more coherent and
contextual responses.
"""
import streamlit as st
from typing import List, Dict, Any, Optional

class ConversationContext:
    """Manages conversation context for the chatbot."""
    
    def __init__(self, max_context_messages: int = 5, max_tokens: int = 1000):
        """Initialize the conversation context manager.
        
        Args:
            max_context_messages: Maximum number of previous messages to include in context
            max_tokens: Approximate maximum number of tokens to include in context
        """
        self.max_context_messages = max_context_messages
        self.max_tokens = max_tokens
        
        # Initialize context in session state if not present
        if "context_summary" not in st.session_state:
            st.session_state.context_summary = ""
    
    def get_context(self, messages: List[Dict[str, Any]]) -> str:
        """Extract relevant context from conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            str: Formatted context string for the LLM
        """
        if not messages or len(messages) < 2:  # Need at least one exchange
            return ""
        
        # Get the most recent messages up to max_context_messages
        recent_messages = messages[-min(len(messages), self.max_context_messages*2):]
        
        # Format messages into a context string
        context_parts = []
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            # Simple token count approximation (words * 1.3)
            token_count = len(content.split()) * 1.3
            
            # Truncate very long messages
            if token_count > self.max_tokens / 2:
                content = content.split()[:int(self.max_tokens/2.6)]
                content = " ".join(content) + "..."
                
            context_parts.append(f"{role}: {content}")
        
        # Join with newlines
        context_text = "\n\n".join(context_parts)
        
        # Add any persistent context summary if it exists
        if st.session_state.context_summary:
            context_text = f"Previous context summary: {st.session_state.context_summary}\n\n" + context_text
        
        return context_text
    
    def update_context_summary(self, summary: str) -> None:
        """Update the persistent context summary.
        
        Args:
            summary: New context summary to store
        """
        st.session_state.context_summary = summary
    
    def get_query_with_context(self, query: str, messages: List[Dict[str, Any]]) -> str:
        """
        Combine the user query with conversation context.
        
        Args:
            query: The current user query
            messages: List of previous messages
            
        Returns:
            str: Query enhanced with conversation context
        """
        context = self.get_context(messages)
        if not context:
            return query
        
        # Combine context with query in a more explicit format
        return f"""
### Conversation History:
{context}

### Current Question: 
{query}

### Instructions:
You MUST use the conversation history to provide context for your answer. 
If the user refers to information from previous messages, use that context in your response.
If the user asks about their name or other personal details mentioned earlier, refer to that information.
Answer the current question taking into account the conversation context.
"""
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        st.session_state.context_summary = ""
