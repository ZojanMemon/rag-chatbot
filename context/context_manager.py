"""Context Manager for the Disaster Management Chatbot.

This module handles conversation context and memory to make the chatbot
aware of previous messages in the conversation.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import re

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
            
        # Initialize personal information storage
        if "personal_info" not in st.session_state:
            st.session_state.personal_info = {}
    
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
        
        # Extract personal information from user messages
        if role == "user":
            self._extract_personal_info(content)
        
        # Trim context if it exceeds max length
        if len(st.session_state.context_history) > self.max_context_length:
            st.session_state.context_history = st.session_state.context_history[-self.max_context_length:]
        
        # Update context summary
        self._update_context_summary()
    
    def _extract_personal_info(self, content: str) -> None:
        """Extract personal information from user messages.
        
        Args:
            content: Message content to extract information from
        """
        # Extract name information
        name_patterns = [
            r"(?:my name is|i am|i'm|call me) ([A-Za-z]+)",
            r"([A-Za-z]+) is my name",
            r"name's ([A-Za-z]+)"
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                name = matches[0].strip().capitalize()
                st.session_state.personal_info["name"] = name
                break
        
        # Extract age information
        age_patterns = [
            r"(?:i am|i'm) (\d+)(?: years old)?",
            r"(\d+) years old"
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                try:
                    age = int(matches[0])
                    st.session_state.personal_info["age"] = age
                except ValueError:
                    pass
                break
        
        # Extract location information
        location_patterns = [
            r"(?:i live in|i am from|i'm from) ([A-Za-z\s,]+)",
            r"(?:living|based) in ([A-Za-z\s,]+)"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, content.lower())
            if matches:
                location = matches[0].strip().capitalize()
                st.session_state.personal_info["location"] = location
                break
    
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
    
    def get_personal_info(self) -> Dict[str, Any]:
        """Get the user's personal information.
        
        Returns:
            Dictionary containing personal information extracted from conversation
        """
        return st.session_state.personal_info
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        st.session_state.context_history = []
        st.session_state.context_summary = ""
        st.session_state.personal_info = {}
    
    def _update_context_summary(self) -> None:
        """Update the context summary based on the conversation history."""
        # Simple implementation: just count messages
        user_messages = sum(1 for msg in st.session_state.context_history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in st.session_state.context_history if msg["role"] == "assistant")
        
        summary = f"Conversation with {user_messages} user messages and {assistant_messages} assistant responses."
        
        # Add personal information to summary if available
        personal_info = st.session_state.personal_info
        if personal_info:
            personal_details = []
            if "name" in personal_info:
                personal_details.append(f"name: {personal_info['name']}")
            if "age" in personal_info:
                personal_details.append(f"age: {personal_info['age']}")
            if "location" in personal_info:
                personal_details.append(f"location: {personal_info['location']}")
            
            if personal_details:
                summary += f" User info: {', '.join(personal_details)}."
        
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
        
        # Add personal information if available
        personal_info = st.session_state.personal_info
        if personal_info:
            context_for_rag += "User personal information:\n"
            for key, value in personal_info.items():
                context_for_rag += f"- User's {key}: {value}\n"
            context_for_rag += "\n"
        
        # Add conversation history
        context_for_rag += "Recent conversation:\n"
        for message in recent_context:
            role_prefix = "User: " if message["role"] == "user" else "Assistant: "
            context_for_rag += f"{role_prefix}{message['content']}\n"
        
        context_for_rag += f"\nCurrent question: {current_query}\n"
        
        # Add special instructions for personal queries
        if "name" in personal_info and any(phrase in current_query.lower() for phrase in ["who am i", "what is my name", "my name"]):
            context_for_rag += f"\nIMPORTANT: The user's name is {personal_info['name']}. Make sure to use this information in your response.\n"
        
        return context_for_rag
