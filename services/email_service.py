"""
Email service for sending chat conversations.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from datetime import datetime


class EmailService:
    def __init__(self):
        """Initialize email service."""
        self.sender_email = st.secrets.get("GMAIL_ADDRESS")
        self.app_password = st.secrets.get("GMAIL_APP_PASSWORD")
        if not self.sender_email or not self.app_password:
            raise ValueError("Email credentials not found")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, recipient_email, chat_history, user_email, emergency_type, user_name="", phone_number="", location=""):
        """Send email silently."""
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = f"🚨 Emergency Assistance Required: {emergency_type}"
            message['From'] = self.sender_email
            message['To'] = recipient_email
            
            # Current time for the email
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            
            # Create the HTML version of the email
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333333;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        background-color: #e74c3c;
                        color: white;
                        padding: 20px;
                        text-align: center;
                        border-radius: 8px 8px 0 0;
                    }}
                    .content {{
                        background-color: #ffffff;
                        padding: 20px;
                        border: 1px solid #e1e1e1;
                        border-radius: 0 0 8px 8px;
                    }}
                    .info-box {{
                        background-color: #f9f9f9;
                        border: 1px solid #e1e1e1;
                        border-radius: 6px;
                        padding: 15px;
                        margin: 15px 0;
                    }}
                    .info-item {{
                        margin: 8px 0;
                    }}
                    .label {{
                        font-weight: bold;
                        color: #555555;
                    }}
                    .chat-history {{
                        margin-top: 20px;
                        border-top: 2px solid #e1e1e1;
                        padding-top: 20px;
                    }}
                    .message {{
                        margin: 10px 0;
                        padding: 10px;
                        border-radius: 6px;
                    }}
                    .user-message {{
                        background-color: #f0f7ff;
                        border-left: 4px solid #3498db;
                    }}
                    .assistant-message {{
                        background-color: #f5f5f5;
                        border-left: 4px solid #95a5a6;
                    }}
                    .timestamp {{
                        color: #888888;
                        font-size: 0.9em;
                        margin-top: 15px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🚨 Emergency Assistance Required</h1>
                        <p style="margin: 0;">Type: {emergency_type}</p>
                    </div>
                    <div class="content">
                        <div class="info-box">
                            <h2 style="margin-top: 0;">Contact Information</h2>
                            <div class="info-item"><span class="label">Name:</span> {user_name or 'Not provided'}</div>
                            <div class="info-item"><span class="label">Email:</span> {user_email}</div>
                            <div class="info-item"><span class="label">Phone:</span> {phone_number or 'Not provided'}</div>
                            <div class="info-item"><span class="label">Location:</span> {location or 'Not provided'}</div>
                        </div>
                        
                        <div class="chat-history">
                            <h2>Conversation History</h2>
            """
            
            # Add each message to the HTML with appropriate styling
            for msg in chat_history:
                role = msg['role'].title()
                content = msg['content']
                message_class = "user-message" if role.lower() == "user" else "assistant-message"
                html += f"""
                            <div class="message {message_class}">
                                <strong>{role}:</strong> {content}
                            </div>
                """
            
            # Close the HTML structure
            html += f"""
                        </div>
                        <div class="timestamp">
                            Sent on {current_time}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version as fallback
            plain_text = f"""
Emergency Assistance Request
--------------------------
Time: {current_time}
Type: {emergency_type}

Contact Information:
- Name: {user_name or 'Not provided'}
- Email: {user_email}
- Phone: {phone_number or 'Not provided'}
- Location: {location or 'Not provided'}

Chat History:
"""
            for msg in chat_history:
                plain_text += f"\n{msg['role'].title()}: {msg['content']}\n"
            
            # Attach both versions
            message.attach(MIMEText(plain_text, 'plain'))
            message.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
                return True, ""
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")  # For debugging
            return False, ""


# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}
