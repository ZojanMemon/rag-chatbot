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
            # Create message container - the correct MIME type is multipart/alternative.
            message = MIMEMultipart('alternative')
            message['Subject'] = f"🚨 Emergency Assistance Required: {emergency_type}"
            # Use the authenticated user's email as the Reply-To address
            message['From'] = f"Disaster Management Assistant <{self.sender_email}>"
            message['Reply-To'] = user_email
            message['To'] = recipient_email
            
            # Current time for the email
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            
            # Clean location string
            location_text = 'Not provided'
            if location and isinstance(location, str):
                location_text = location.strip()
                # Remove any emoji prefixes
                if location_text.startswith('✅ '):
                    location_text = location_text[2:].strip()
                elif location_text.startswith('📍 '):
                    location_text = location_text[2:].strip()
            
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
- Location: {location_text}

Chat History:
"""
            for msg in chat_history:
                plain_text += f"\n{msg['role'].title()}: {msg['content']}\n"
            
            # Create the HTML version
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    /* Reset styles */
                    * {{
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }}
                    
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                        line-height: 1.6;
                        color: #333333;
                        background-color: #f5f5f5;
                        margin: 0;
                        padding: 0;
                    }}
                    
                    .email-wrapper {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: #ffffff;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    }}
                    
                    .header {{
                        background-color: #dc3545;
                        color: white;
                        padding: 24px;
                        text-align: center;
                    }}
                    
                    .header h1 {{
                        margin: 0;
                        font-size: 24px;
                        font-weight: 600;
                    }}
                    
                    .header p {{
                        margin: 8px 0 0 0;
                        opacity: 0.9;
                    }}
                    
                    .content {{
                        padding: 24px;
                    }}
                    
                    .info-box {{
                        background-color: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 6px;
                        padding: 20px;
                        margin-bottom: 24px;
                    }}
                    
                    .info-box h2 {{
                        color: #2c3e50;
                        font-size: 18px;
                        margin-bottom: 16px;
                        font-weight: 600;
                    }}
                    
                    .info-item {{
                        margin: 12px 0;
                        display: flex;
                        align-items: baseline;
                    }}
                    
                    .label {{
                        font-weight: 600;
                        color: #495057;
                        width: 100px;
                        flex-shrink: 0;
                    }}
                    
                    .value {{
                        color: #212529;
                    }}
                    
                    .chat-history {{
                        border-top: 2px solid #e9ecef;
                        padding-top: 24px;
                        margin-top: 24px;
                    }}
                    
                    .chat-history h2 {{
                        color: #2c3e50;
                        font-size: 18px;
                        margin-bottom: 16px;
                        font-weight: 600;
                    }}
                    
                    .message {{
                        margin: 16px 0;
                        padding: 12px 16px;
                        border-radius: 8px;
                        position: relative;
                    }}
                    
                    .user-message {{
                        background-color: #e3f2fd;
                        border: 1px solid #bbdefb;
                        margin-left: 16px;
                    }}
                    
                    .assistant-message {{
                        background-color: #f5f5f5;
                        border: 1px solid #e0e0e0;
                        margin-right: 16px;
                    }}
                    
                    .message strong {{
                        color: #1976d2;
                        display: block;
                        margin-bottom: 4px;
                        font-size: 14px;
                    }}
                    
                    .timestamp {{
                        text-align: center;
                        color: #6c757d;
                        font-size: 14px;
                        margin-top: 24px;
                        padding-top: 16px;
                        border-top: 1px solid #e9ecef;
                    }}
                </style>
            </head>
            <body>
                <div class="email-wrapper">
                    <div class="header">
                        <h1>🚨 Emergency Assistance Required</h1>
                        <p>Type: {emergency_type}</p>
                    </div>
                    <div class="content">
                        <div class="info-box">
                            <h2>Contact Information</h2>
                            <div class="info-item">
                                <span class="label">Name:</span>
                                <span class="value">{user_name or 'Not provided'}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Email:</span>
                                <span class="value">{user_email}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Phone:</span>
                                <span class="value">{phone_number or 'Not provided'}</span>
                            </div>
                            <div class="info-item">
                                <span class="label">Location:</span>
                                <span class="value">{location_text}</span>
                            </div>
                        </div>
                        
                        <div class="chat-history">
                            <h2>Chat History</h2>
                            {self._format_chat_history(chat_history)}
                        </div>
                        
                        <div class="timestamp">
                            Sent on {current_time}
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Turn these into plain/html MIMEText objects
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(html, 'html')

            # Add HTML/plain-text parts to MIMEMultipart message
            # The email client will try to render the last part first
            message.attach(part1)
            message.attach(part2)

            # Create SMTP session
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.app_password)
                server.send_message(message)
            
            return True, None
        except Exception as e:
            return False, str(e)

    def _format_chat_history(self, chat_history):
        """Format chat history as HTML."""
        html = ""
        for msg in chat_history:
            role = msg['role']
            content = msg['content']
            
            # Determine message class based on role
            msg_class = "user-message" if role == "user" else "assistant-message"
            role_title = "You" if role == "user" else "Assistant"
            
            html += f"""
            <div class="message {msg_class}">
                <strong>{role_title}</strong>
                {content}
            </div>
            """
        return html


# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.response@example.com",
    "Fire": "fire.department@example.com",
    "Medical": "medical.emergency@example.com",
    "General": "general.emergency@example.com"
}
