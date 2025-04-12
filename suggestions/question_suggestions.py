"""Question suggestions module for the disaster management chatbot.

This module provides functionality to display suggested questions
for new conversations, enhancing user experience by offering
quick-start options for common disaster management queries.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
import random

# Categories of suggested questions with multilingual support
SUGGESTED_QUESTIONS = {
    "English": {
        "Preparation": [
            "How can I prepare for a flood?",
            "What should be in my emergency kit?",
            "How do I create a family emergency plan?"
        ],
        "Response": [
            "What should I do during an earthquake?",
            "How can I help others during a disaster?",
            "What are the signs of heat stroke?"
        ],
        "Recovery": [
            "How do I clean up after a flood?",
            "What assistance is available after a disaster?",
            "How can I help my community recover?"
        ]
    },
    "Urdu": {
        "Preparation": [
            "سیلاب کے لیے میں کیسے تیاری کر سکتا ہوں؟",
            "میرے ایمرجنسی کٹ میں کیا ہونا چاہیے؟",
            "میں خاندانی ایمرجنسی پلان کیسے بناؤں؟"
        ],
        "Response": [
            "زلزلے کے دوران مجھے کیا کرنا چاہیے؟",
            "آفت کے دوران میں دوسروں کی مدد کیسے کر سکتا ہوں؟",
            "گرمی کے اثرات کی علامات کیا ہیں؟"
        ],
        "Recovery": [
            "سیلاب کے بعد صفائی کیسے کروں؟",
            "آفت کے بعد کون سی مدد دستیاب ہے؟",
            "میں اپنی کمیونٹی کی بحالی میں کیسے مدد کر سکتا ہوں؟"
        ]
    },
    "Sindhi": {
        "Preparation": [
            "ٻوڏ لاءِ مان ڪيئن تياري ڪري سگھان ٿو؟",
            "منهنجي ايمرجنسي ڪٽ ۾ ڇا هجڻ گھرجي؟",
            "مان خانداني ايمرجنسي پلان ڪيئن ٺاهيان؟"
        ],
        "Response": [
            "زلزلي دوران مون کي ڇا ڪرڻ گھرجي؟",
            "آفت دوران مان ٻين جي مدد ڪيئن ڪري سگھان ٿو؟",
            "گرمي جي اثرن جون نشانيون ڇا آهن؟"
        ],
        "Recovery": [
            "ٻوڏ کان پوءِ صفائي ڪيئن ڪريان؟",
            "آفت کان پوءِ ڪهڙي مدد دستياب آهي؟",
            "مان پنهنجي ڪميونٽي جي بحالي ۾ ڪيئن مدد ڪري سگھان ٿو؟"
        ]
    }
}

# CSS for styling the suggestion buttons
SUGGESTION_CSS = """
<style>
.suggestion-container {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 20px;
    justify-content: center;
}

.suggestion-category {
    width: 100%;
    margin-bottom: 5px;
    text-align: center;
    color: #9e9e9e;
    font-size: 0.85rem;
    font-weight: 500;
}

.suggestion-button {
    background-color: rgba(49, 51, 63, 0.2);
    border-radius: 12px;
    border: 1px solid rgba(49, 51, 63, 0.2);
    color: #fafafa;
    cursor: pointer;
    padding: 10px 15px;
    text-align: center;
    transition: all 0.3s ease;
    font-size: 0.9rem;
    flex: 1 1 auto;
    min-width: 150px;
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.suggestion-button:hover {
    background-color: rgba(49, 51, 63, 0.4);
    border-color: rgba(49, 51, 63, 0.4);
    transform: translateY(-2px);
    box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
    .suggestion-button {
        min-width: 120px;
        font-size: 0.8rem;
        padding: 8px 12px;
    }
}
</style>
"""

def get_suggested_questions(language: str = "English") -> Dict[str, List[str]]:
    """Get suggested questions in the specified language.
    
    Args:
        language: The language to get questions for
        
    Returns:
        Dictionary of categories and their questions
    """
    if language not in SUGGESTED_QUESTIONS:
        language = "English"  # Fallback to English
    
    return SUGGESTED_QUESTIONS[language]

def display_question_suggestions():
    """Display question suggestion buttons for new conversations.
    
    This function should only be called when:
    1. The conversation is new (no messages yet)
    2. The user hasn't interacted with the chat yet
    """
    # Only show suggestions for new conversations
    if st.session_state.get("messages", []) or st.session_state.get("suggestions_clicked", False):
        return
    
    # Mark that we've shown suggestions to avoid showing them again
    st.session_state.suggestions_clicked = False
    
    # Get language-appropriate suggestions
    language = st.session_state.get("input_language", "English")
    suggestions = get_suggested_questions(language)
    
    # Display the styled suggestion buttons
    st.markdown(SUGGESTION_CSS, unsafe_allow_html=True)
    
    # Container for all suggestions
    st.markdown('<div class="suggestion-container">', unsafe_allow_html=True)
    
    # Display each category and its questions
    for category, questions in suggestions.items():
        # Category heading
        st.markdown(f'<div class="suggestion-category">{category}</div>', unsafe_allow_html=True)
        
        # Create buttons for each question in this category
        cols = st.columns(len(questions))
        for i, question in enumerate(questions):
            button_key = f"suggestion_{category}_{i}"
            if cols[i].button(question, key=button_key):
                # Set the clicked question as the user input
                st.session_state.suggestions_clicked = True
                st.session_state.user_input = question
                # Force a rerun to process the selected question
                st.rerun()
    
    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)

def handle_suggestion_click(question: str):
    """Handle when a user clicks on a suggested question.
    
    Args:
        question: The question that was clicked
    """
    # Set the clicked question as the user input
    st.session_state.user_input = question
    st.session_state.suggestions_clicked = True
