"""
Email service for sending chat conversations to disaster management authorities.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import streamlit as st

class EmailService:
    def __init__(self):
        """Initialize email service with Gmail SMTP settings."""
        try:
            # Try getting from Streamlit secrets first
            self.sender_email = st.secrets["GMAIL_ADDRESS"]
            self.app_password = st.secrets["GMAIL_APP_PASSWORD"]
            st.write(f"Debug: Initialized with sender email: {self.sender_email}")
        except Exception as e:
            st.error(f"Error loading credentials: {str(e)}")
            raise ValueError(f"Failed to load Gmail credentials: {str(e)}")
        
        # SMTP Settings for Gmail
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, recipient_email, chat_history, user_email, emergency_type):
        """Send email using Gmail SMTP."""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            subject = f"Emergency Assistance Required: {emergency_type}"
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            # Create HTML content
            html_content = f"""
            <html>
                <body>
                    <h2>Emergency Assistance Request</h2>
                    <p><strong>From User:</strong> {user_email}</p>
                    <p><strong>Emergency Type:</strong> {emergency_type}</p>
                    <h3>Chat History:</h3>
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                    {"<br>".join(f"{msg['role'].title()}: {msg['content']}" for msg in chat_history)}
                    </div>
                </body>
            </html>
            """
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)
            
            # Debug information
            st.write("---")
            st.write("📧 Email Details:")
            st.write(f"From: {self.sender_email}")
            st.write(f"To: {recipient_email}")
            st.write(f"Subject: {subject}")
            
            # Connect and send
            st.write("Connecting to SMTP server...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                st.write("Starting TLS connection...")
                server.starttls()
                st.write("Logging in...")
                server.login(self.sender_email, self.app_password)
                st.write("Sending email...")
                server.send_message(message)
                st.write("✅ Email sent successfully!")
            
            return True, "Email sent successfully!"
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "Gmail authentication failed. Please check your app password."
            st.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            st.error(f"Error type: {type(e).__name__}")
            st.error(error_msg)
            return False, error_msg

# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}
