"""Question suggestions for new conversations.

This module provides functionality to display suggested questions
for users at the beginning of new conversations.
"""

import streamlit as st
from typing import List, Callable
import json
import os

# Default suggested questions in different languages
DEFAULT_SUGGESTIONS = {
    "English": [
        "What should I do during a flood emergency?",
        "How can I prepare an emergency kit for disasters?",
        "What are the signs of an approaching earthquake?"
    ],
    "Urdu": [
        "سیلاب کی ہنگامی صورتحال میں مجھے کیا کرنا چاہیے؟",
        "آفات کے لیے ہنگامی کٹ کیسے تیار کروں؟",
        "زلزلے کے آنے کی علامات کیا ہیں؟"
    ],
    "Sindhi": [
        "ٽوڙ جي ايمرجنسي ۾ مون کي ڇا ڪرڻ گھرجي؟",
        "آفتن لاءِ ايمرجنسي ڪٽ ڪيئن تيار ڪجي؟",
        "زلزلي جي اچڻ جون نشانيون ڇا آهن؟"
    ]
}


class QuestionSuggestions:
    """Manages question suggestions for new conversations."""
    
    def __init__(self):
        """Initialize the question suggestions manager."""
        self.suggestions_file = os.path.join(os.path.dirname(__file__), "custom_suggestions.json")
        self.load_suggestions()
    
    def load_suggestions(self) -> None:
        """Load custom suggestions if available, otherwise use defaults."""
        try:
            if os.path.exists(self.suggestions_file):
                with open(self.suggestions_file, "r", encoding="utf-8") as f:
                    self.suggestions = json.load(f)
            else:
                self.suggestions = DEFAULT_SUGGESTIONS
        except Exception as e:
            st.error(f"Error loading suggestions: {str(e)}")
            self.suggestions = DEFAULT_SUGGESTIONS
    
    def save_suggestions(self) -> None:
        """Save custom suggestions to file."""
        try:
            with open(self.suggestions_file, "w", encoding="utf-8") as f:
                json.dump(self.suggestions, f, ensure_ascii=False, indent=4)
        except Exception as e:
            st.error(f"Error saving suggestions: {str(e)}")
    
    def get_suggestions(self, language: str) -> List[str]:
        """Get suggestions for the specified language.
        
        Args:
            language: The language to get suggestions for
            
        Returns:
            List of suggested questions in the specified language
        """
        if language in self.suggestions:
            return self.suggestions[language]
        return self.suggestions["English"]  # Fallback to English
    
    def display_suggestions(self, language: str, on_click_callback: Callable[[str], None]) -> None:
        """Display question suggestions as clickable buttons.
        
        Args:
            language: The language to display suggestions for
            on_click_callback: Function to call when a suggestion is clicked
        """
        suggestions = self.get_suggestions(language)
        
        st.markdown("### 💡 Suggested Questions")
        
        # Create a container with custom styling for the suggestions
        suggestion_container = st.container()
        with suggestion_container:
            # Apply custom CSS for better styling
            st.markdown("""
            <style>
            .suggestion-btn {
                background-color: rgba(49, 51, 63, 0.2);
                border-radius: 12px;
                border: 1px solid rgba(49, 51, 63, 0.2);
                color: inherit;
                padding: 10px 15px;
                margin-bottom: 10px;
                cursor: pointer;
                text-align: left;
                transition: all 0.3s ease;
                width: 100%;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            .suggestion-btn:hover {
                border-color: #4e8df5;
                background-color: rgba(78, 141, 245, 0.1);
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create columns for better layout
            cols = st.columns(1)
            
            # Display each suggestion as a button
            for i, suggestion in enumerate(suggestions):
                # Create a unique key for each button
                key = f"suggestion_{i}_{language}"
                
                # Create a button with custom styling
                if cols[0].button(suggestion, key=key, use_container_width=True):
                    on_click_callback(suggestion)


# Initialize the suggestions manager
suggestions_manager = QuestionSuggestions()


def show_suggestions(language: str, on_click_callback: Callable[[str], None]) -> None:
    """Show question suggestions if this is a new conversation.
    
    Args:
        language: The language to display suggestions in
        on_click_callback: Function to call when a suggestion is clicked
    """
    # Only show suggestions for new conversations with no messages
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        suggestions_manager.display_suggestions(language, on_click_callback)
