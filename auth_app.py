"""
Disaster Management Assistant with User Authentication
This version of the app includes user authentication and chat history persistence.
"""
import streamlit as st
import importlib
import sys
from datetime import datetime
from auth.authenticator import FirebaseAuthenticator
from auth.chat_history import ChatHistoryManager
from auth.ui import auth_page, user_sidebar, chat_history_sidebar, sync_chat_message, load_user_preferences, save_user_preferences

# Set page config
st.set_page_config(
    page_title="Disaster Management Assistant",
    page_icon="🆘",
    layout="wide"
)

# Initialize session state for chat history if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_language" not in st.session_state:
    st.session_state.input_language = "English"
if "output_language" not in st.session_state:
    st.session_state.output_language = "English"

def main():
    """Main application function with authentication."""
    st.title("Disaster Management Assistant 🆘")
    
    # Handle authentication
    is_authenticated, user = auth_page()
    
    if not is_authenticated:
        # Show welcome message for non-authenticated users
        st.markdown("""
        ## Welcome to the Disaster Management Assistant
        
        Please log in or create an account to access the chatbot and save your chat history.
        
        This assistant can help you with:
        - Emergency preparedness
        - Disaster response procedures
        - Safety protocols
        - And more...
        """)
        return
    
    # User is authenticated
    user_id = user['uid']
    
    # Load user preferences
    preferences = load_user_preferences(user)
    
    # Display user sidebar with chat history
    user_sidebar(user)
    chat_history_sidebar(user_id)
    
    # Import the original app's functionality
    # This approach prevents modifying the original app.py
    sys.path.insert(0, '.')
    try:
        # Import only the necessary functions from app.py
        app_module = importlib.import_module('app')
        initialize_rag = getattr(app_module, 'initialize_rag')
        get_rag_response = getattr(app_module, 'get_rag_response')
        is_general_chat = getattr(app_module, 'is_general_chat')
        get_general_response = getattr(app_module, 'get_general_response')
        
        # Initialize RAG system
        qa_chain = initialize_rag()
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask a question about disaster management..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            # Save to Firebase
            metadata = {
                'language': st.session_state.input_language,
                'timestamp': datetime.now().isoformat()
            }
            sync_chat_message(user_id, "user", prompt, metadata)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                
                try:
                    # Check if it's a general chat query
                    if is_general_chat(prompt):
                        response = get_general_response(prompt)
                    else:
                        # Use RAG for domain-specific questions
                        response = get_rag_response(qa_chain, prompt)
                    
                    # Display response
                    message_placeholder.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Save to Firebase
                    metadata = {
                        'language': st.session_state.output_language,
                        'timestamp': datetime.now().isoformat(),
                        'type': 'general' if is_general_chat(prompt) else 'rag'
                    }
                    sync_chat_message(user_id, "assistant", response, metadata)
                    
                except Exception as e:
                    error_message = f"Error generating response: {str(e)}"
                    message_placeholder.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
        
        # Save user preferences when they change
        if 'last_input_language' not in st.session_state:
            st.session_state.last_input_language = st.session_state.input_language
        if 'last_output_language' not in st.session_state:
            st.session_state.last_output_language = st.session_state.output_language
            
        # Check if preferences changed
        if (st.session_state.last_input_language != st.session_state.input_language or
            st.session_state.last_output_language != st.session_state.output_language):
            save_user_preferences(user_id)
            st.session_state.last_input_language = st.session_state.input_language
            st.session_state.last_output_language = st.session_state.output_language
    
    except Exception as e:
        st.error(f"Error loading application: {str(e)}")

if __name__ == "__main__":
    main()
