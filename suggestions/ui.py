"""UI components for question suggestions in the disaster management chatbot.

This module provides the UI components for displaying suggested questions
in the chat interface, enhancing user experience with quick-start options.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from .question_suggestions import get_suggested_questions, SUGGESTION_CSS

def render_suggestion_buttons():
    """Render suggestion buttons in a visually appealing way.
    
    This function should be called at the beginning of the chat interface,
    before any messages are displayed.
    """
    # Only show suggestions for new conversations
    if st.session_state.get("messages", []) or st.session_state.get("suggestions_clicked", False):
        return
    
    # Get language-appropriate suggestions
    language = st.session_state.get("input_language", "English")
    suggestions = get_suggested_questions(language)
    
    # Display the styled suggestion buttons
    st.markdown(SUGGESTION_CSS, unsafe_allow_html=True)
    
    # Create a container for better spacing
    with st.container():
        # Add a small heading for the suggestions
        st.markdown(f"<h4 style='text-align: center; color: #9e9e9e; font-size: 1rem; margin-bottom: 15px;'>Try asking about...</h4>", unsafe_allow_html=True)
        
        # Container for all suggestions
        st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
        
        # Display each category and its questions
        for category, questions in suggestions.items():
            # Category heading
            st.markdown(f'<div class="suggestion-category">{category}</div>', unsafe_allow_html=True)
            
            # Create a row of buttons for each question in this category
            cols = st.columns(len(questions))
            for i, question in enumerate(questions):
                button_key = f"suggestion_{category}_{i}_{language}"
                if cols[i].button(question, key=button_key):
                    # Set the clicked question as the user input
                    st.session_state.suggestions_clicked = True
                    st.session_state.user_input = question
                    # Force a rerun to process the selected question
                    st.rerun()
        
        # Close the container
        st.markdown('</div>', unsafe_allow_html=True)

def initialize_suggestion_state():
    """Initialize the suggestion state in the session.
    
    This should be called during app initialization.
    """
    if "suggestions_clicked" not in st.session_state:
        st.session_state.suggestions_clicked = False

def reset_suggestions():
    """Reset the suggestion state to show suggestions again.
    
    This should be called when starting a new conversation.
    """
    st.session_state.suggestions_clicked = False
