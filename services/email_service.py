"""
Email service for sending chat conversations.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


class EmailService:
    def __init__(self):
        """Initialize email service."""
        self.sender_email = st.secrets.get("GMAIL_ADDRESS")
        self.app_password = st.secrets.get("GMAIL_APP_PASSWORD")
        if not self.sender_email or not self.app_password:
            raise ValueError("Email credentials not found")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, recipient_email, chat_history, user_email, emergency_type):
        """Send email silently."""
        try:
            message = MIMEMultipart()
            message['Subject'] = f"Emergency Assistance Required: {emergency_type}"
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            body = f"""
Emergency Assistance Request
--------------------------
From User: {user_email}
Emergency Type: {emergency_type}

Chat History:
"""
            for msg in chat_history:
                body += f"\n{msg['role'].title()}: {msg['content']}\n"
            
            message.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
                return True, ""
            
        except Exception:
            return False, ""


# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}
