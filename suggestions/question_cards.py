"""Question cards component for the disaster management chatbot.

This module provides a component that displays clickable question cards
at the beginning of new conversations to help users get started.
"""
import streamlit as st
from typing import List, Dict, Callable
import random
from .card_styles import get_card_css

# Sample questions for different categories
DISASTER_QUESTIONS = {
    "Floods": [
        "What should I do during a flood?",
        "How can I prepare my home for a flood?",
        "What are the warning signs of a flood?"
    ],
    "Earthquakes": [
        "How should I protect myself during an earthquake?",
        "What supplies should I have in my earthquake kit?",
        "What should I do after an earthquake?"
    ],
    "Cyclones": [
        "How can I prepare for a cyclone?",
        "What are the safety measures during a cyclone?",
        "How do I secure my home against cyclone damage?"
    ],
    "General": [
        "What emergency contacts should I save?",
        "How do I create a family emergency plan?",
        "What should be in a basic emergency kit?"
    ],
    "Evacuation": [
        "When should I evacuate my home?",
        "What's the safest evacuation route in my area?",
        "What should I take when evacuating?"
    ]
}

# Multilingual welcome messages
WELCOME_MESSAGES = {
    "English": {
        "title": "Hi, I'm your Disaster Management Assistant",
        "subtitle": "How can I help you today? You can ask me a question or click on one of the suggestions below."
    },
    "Urdu": {
        "title": "ہیلو، میں آپ کا آفات سے نمٹنے والا اسسٹنٹ ہوں",
        "subtitle": "میں آج آپ کی کیسے مدد کر سکتا ہوں؟ آپ مجھ سے سوال پوچھ سکتے ہیں یا نیچے دیئے گئے تجاویز میں سے کسی ایک پر کلک کر سکتے ہیں۔"
    },
    "Sindhi": {
        "title": "هائي، آئون توهان جو آفتن جي انتظام ۾ مددگار آهيان",
        "subtitle": "آئون اڄ توهان جي ڪيئن مدد ڪري سگھان ٿو؟ توهان مون کان سوال پڇي سگھو ٿا يا هيٺ ڏنل تجويزن مان ڪنهن هڪ تي ڪلڪ ڪري سگھو ٿا۔"
    }
}

def get_random_questions(num_questions: int = 4) -> List[str]:
    """Get a random selection of questions from different categories.
    
    Args:
        num_questions: Number of questions to select
        
    Returns:
        List of randomly selected questions
    """
    all_questions = []
    for category, questions in DISASTER_QUESTIONS.items():
        all_questions.extend(questions)
    
    # Ensure we don't try to select more questions than available
    num_to_select = min(num_questions, len(all_questions))
    
    return random.sample(all_questions, num_to_select)

def render_question_cards(on_card_click: Callable[[str], None]) -> None:
    """Render the question cards component.
    
    Args:
        on_card_click: Callback function to handle card clicks
    """
    # Get the appropriate welcome message based on language
    language = st.session_state.get("output_language", "English")
    welcome = WELCOME_MESSAGES.get(language, WELCOME_MESSAGES["English"])
    
    # Inject CSS
    st.markdown(get_card_css(), unsafe_allow_html=True)
    
    # Welcome header
    st.markdown(f"""
    <div class="welcome-header">
        <h2>{welcome['title']}</h2>
        <p>{welcome['subtitle']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get random questions
    questions = get_random_questions(4)
    
    # Create question cards HTML
    cards_html = '<div class="question-cards-container">'
    
    for i, question in enumerate(questions):
        # Create a unique key for each card
        card_key = f"question_card_{i}"
        
        cards_html += f"""
        <div class="question-card" onclick="parent.postMessage({{'question': '{question}'}}, '*')" id="{card_key}" tabindex="0" role="button" aria-label="Ask: {question}">
            <h4>{question}</h4>
            <p>Click to ask</p>
        </div>
        """
    
    cards_html += '</div>'
    
    # Render the cards
    st.markdown(cards_html, unsafe_allow_html=True)
    
    # JavaScript to handle card clicks
    st.markdown("""
    <script>
    window.addEventListener('message', function(e) {
        if (e.data.question) {
            // Find the Streamlit message to send the question
            const textareas = parent.document.querySelectorAll('textarea');
            const submitButtons = parent.document.querySelectorAll('button[kind="primaryFormSubmit"]');
            
            if (textareas.length > 0 && submitButtons.length > 0) {
                const textarea = textareas[0];
                const submitButton = submitButtons[0];
                
                // Set the value and dispatch events
                textarea.value = e.data.question;
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Submit the form
                setTimeout(() => {
                    submitButton.click();
                }, 100);
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)

def should_show_question_cards() -> bool:
    """Determine if question cards should be shown.
    
    Returns:
        True if cards should be shown, False otherwise
    """
    # Show cards only if this is a new conversation (no messages)
    # or if there's only a single welcome message
    messages = st.session_state.get("messages", [])
    
    if not messages:
        return True
    
    if len(messages) == 1 and messages[0]["role"] == "assistant":
        # Check if it's the initial greeting message
        return True
    
    return False
