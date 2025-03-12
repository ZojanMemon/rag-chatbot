"""Email sharing component for the chatbot."""
import streamlit as st
from services.email_service import EmailService

def show_email_ui(messages, user_email="Anonymous"):
    """Display the email sharing interface."""
    # Only show after some conversation
    if len(messages) < 2:
        return

    # Create container for email UI
    email_container = st.container()
    
    with email_container:
        st.markdown("---")  # Visual separator
        
        # Email sharing section
        st.markdown("### 📧 Share with Authorities")
        st.info("Share this conversation with relevant authorities for immediate assistance.")
        
        # Emergency type selection
        emergency_types = {
            "Flood": "themusicking151@gmail.com",
            "Earthquake": "themusicking151@gmail.com",
            "Fire": "themusicking151@gmail.com",
            "Medical": "themusicking151@gmail.com",
            "General": "themusicking151@gmail.com"
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            emergency_type = st.selectbox(
                "Select Emergency Type",
                options=list(emergency_types.keys()),
                key="share_emergency_type"
            )
        
        with col2:
            if st.button("📤 Share", type="primary", use_container_width=True):
                try:
                    with st.spinner("Sending..."):
                        email_service = EmailService()
                        success, message = email_service.send_email(
                            recipient_email=emergency_types[emergency_type],
                            chat_history=messages,
                            user_email=user_email,
                            emergency_type=emergency_type
                        )
                        
                        if success:
                            st.success(f"✅ Shared with {emergency_type} authorities")
                        else:
                            st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
