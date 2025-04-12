"""Handler for question card interactions.

This module provides utilities to handle the interaction between
the question cards and the chat interface.
"""
import streamlit as st
from typing import List, Dict, Any, Callable

def handle_card_click(question: str) -> None:
    """Handle a click on a question card.
    
    This function simulates a user sending the question from the card.
    
    Args:
        question: The question text from the clicked card
    """
    # Add the question to the messages as if the user typed it
    if "messages" in st.session_state:
        st.session_state.messages.append({"role": "user", "content": question})
        
        # Set the submitted flag to trigger processing in the main app
        st.session_state.submitted = True
        
        # Clear any previous thinking state
        st.session_state.thinking = False

def register_streamlit_handler() -> None:
    """Register a Streamlit session state handler for card clicks.
    
    This function sets up the necessary session state variables to handle
    communication between the JavaScript in the cards and the Streamlit app.
    """
    # Initialize the session state variables if they don't exist
    if "card_clicked" not in st.session_state:
        st.session_state.card_clicked = False
        
    if "card_question" not in st.session_state:
        st.session_state.card_question = ""
        
    # Check if a card was clicked (this would be set by JavaScript)
    if st.session_state.card_clicked and st.session_state.card_question:
        # Handle the click
        handle_card_click(st.session_state.card_question)
        
        # Reset the state
        st.session_state.card_clicked = False
        st.session_state.card_question = ""
