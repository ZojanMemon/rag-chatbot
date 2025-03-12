"""
Email service for sending chat conversations to disaster management authorities.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


class EmailService:
    def __init__(self):
        """Initialize email service with Gmail SMTP settings."""
        try:
            # Get email credentials
            self.sender_email = st.secrets.get("GMAIL_ADDRESS")
            self.app_password = st.secrets.get("GMAIL_APP_PASSWORD")
            
            # Validate credentials
            if not self.sender_email:
                raise ValueError("GMAIL_ADDRESS not found in secrets")
            if not self.app_password:
                raise ValueError("GMAIL_APP_PASSWORD not found in secrets")
                
            # SMTP Settings
            self.smtp_server = "smtp.gmail.com"
            self.smtp_port = 587
            
        except Exception as e:
            st.error(f"Failed to initialize email service: {str(e)}")
            raise

    def send_email(self, recipient_email, chat_history, user_email, emergency_type):
        """Send email using Gmail SMTP."""
        try:
            # Validate inputs
            if not recipient_email:
                raise ValueError("Recipient email is required")
            if not chat_history:
                raise ValueError("Chat history is empty")
            
            # Create message
            message = MIMEMultipart()
            message['Subject'] = f"Emergency Assistance Required: {emergency_type}"
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            # Create email body
            body = f"""
Emergency Assistance Request
--------------------------
From User: {user_email}
Emergency Type: {emergency_type}

Chat History:
"""
            
            # Add chat history
            for msg in chat_history:
                body += f"\n{msg['role'].title()}: {msg['content']}\n"
            
            # Attach body
            message.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
                st.success("✅ Email sent successfully!")
                return True, "Email sent successfully!"
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = "Failed to authenticate with Gmail. Please check your app password."
            st.error(error_msg)
            st.error(f"SMTP Error: {str(e)}")
            return False, error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            st.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            st.error(error_msg)
            st.error(f"Error type: {type(e).__name__}")
            return False, error_msg

# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}
