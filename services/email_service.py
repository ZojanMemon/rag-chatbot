"""
Email service for sending chat conversations to disaster management authorities.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

class EmailService:
    def __init__(self):
        """Initialize email service with Gmail SMTP settings."""
        self.sender_email = os.getenv('GMAIL_ADDRESS') or st.secrets.get("GMAIL_ADDRESS")
        self.app_password = os.getenv('GMAIL_APP_PASSWORD') or st.secrets.get("GMAIL_APP_PASSWORD")
        
        if not self.sender_email or not self.app_password:
            raise ValueError("Gmail credentials not found. Please check your environment variables or Streamlit secrets.")
        
        # SMTP Settings for Gmail
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def format_chat_history(self, chat_history):
        """Format chat history into a readable email body."""
        formatted_chat = []
        for message in chat_history:
            role = "User" if message.get("role") == "user" else "Chatbot"
            content = message.get("content", "")
            formatted_chat.append(f"{role}: {content}\n")
        return "\n".join(formatted_chat)

    def create_email_content(self, chat_history, user_email, emergency_type):
        """Create email subject and body."""
        subject = f"Emergency Assistance Required: {emergency_type}"
        
        # Create HTML email body
        html_content = f"""
        <html>
            <body>
                <h2>Emergency Assistance Request</h2>
                <p><strong>From User:</strong> {user_email}</p>
                <p><strong>Emergency Type:</strong> {emergency_type}</p>
                <h3>Chat History:</h3>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                    {self.format_chat_history(chat_history).replace('\n', '<br>')}
                </div>
                <p>This is an automated email from the Disaster Management Chatbot.</p>
            </body>
        </html>
        """
        
        return subject, html_content

    def send_email(self, recipient_email, chat_history, user_email, emergency_type):
        """Send email using Gmail SMTP."""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            subject, html_content = self.create_email_content(chat_history, user_email, emergency_type)
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Connect to Gmail SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
            
            return True, "Email sent successfully!"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"

# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}
