import streamlit as st
from services.email_service import EmailService

def main():
    st.title("Email Service Test")
    
    # Initialize email service
    email_service = EmailService()
    
    # Display available secrets for debugging
    st.write("## Debug Information")
    st.write("Available secrets:", list(st.secrets.keys()))
    
    # Test email form
    st.write("## Send Test Email")
    recipient_email = st.text_input("Recipient Email", "themusicking151@gmail.com")
    
    # Sample chat history
    chat_history = [
        {"role": "user", "content": "This is a test message from Streamlit Cloud"},
        {"role": "assistant", "content": "This is a test response from the chatbot"}
    ]
    
    if st.button("Send Test Email"):
        success, message = email_service.send_email(
            recipient_email=recipient_email,
            chat_history=chat_history,
            user_email="test@example.com",
            emergency_type="Test"
        )
        
        if success:
            st.success(message)
        else:
            st.error(message)

if __name__ == "__main__":
    main()
