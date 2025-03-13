"""
Email service for sending chat history to authorities.
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import streamlit as st
import os
import json

class EmailService:
    """Email service for sending chat history to authorities."""

    def __init__(self):
        """Initialize the email service with Gmail SMTP settings."""
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        # Get credentials from Streamlit secrets
        self.sender_email = st.secrets.get("GMAIL_ADDRESS")
        self.password = st.secrets.get("GMAIL_APP_PASSWORD")
        if not self.sender_email or not self.password:
            # Fallback to environment variables for development
            import os
            self.sender_email = os.environ.get("EMAIL_USER", "themusicking151@gmail.com")
            self.password = os.environ.get("EMAIL_PASSWORD", "xoqz qqkf wkqm ycgc")

    def format_chat_history(self, messages):
        """Format chat history for email."""
        html = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                html += f"""
                <div class="message user-message">
                    <strong>You</strong>
                    {content}
                </div>
                """
            elif role == "assistant":
                html += f"""
                <div class="message assistant-message">
                    <strong>Assistant</strong>
                    {content}
                </div>
                """
        return html

    def create_email_content(self, chat_history, emergency_type, user_name, phone_number, location, user_email):
        """Create the email content with chat history and user details."""
        formatted_history = self.format_chat_history(chat_history)
        
        # Clean location data
        clean_location = "Not provided"
        if location:
            if isinstance(location, str):
                # Remove any emoji prefixes if present
                if "✅" in location:
                    location = location.split("✅", 1)[1].strip()
                clean_location = location
        
        # Current date and time
        current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # HTML content
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
                    display: grid;
                    grid-template-columns: 120px 1fr;
                    align-items: flex-start;
                }}
                
                .label {{
                    font-weight: 600;
                    color: #495057;
                    padding-top: 2px;
                }}
                
                .value {{
                    color: #212529;
                    padding-top: 2px;
                    padding-left: 60px !important;
                }}

                /* Additional specificity for email clients */
                [class~="value"],
                .info-item .value,
                .info-box .value {{
                    padding-left: 60px !important;
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
                            <span class="label">Name</span>
                            <span class="value">{user_name or 'Not provided'}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Email</span>
                            <span class="value">{user_email}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Phone</span>
                            <span class="value">{phone_number or 'Not provided'}</span>
                        </div>
                        <div class="info-item">
                            <span class="label">Location</span>
                            <span class="value">{clean_location}</span>
                        </div>
                    </div>
                    
                    <div class="chat-history">
                        <h2>Chat History</h2>
                        {formatted_history}
                    </div>
                    
                    <div class="timestamp">
                        Sent on {current_time}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def send_email(self, recipient_email, chat_history, user_email, emergency_type, user_name="", phone_number="", location=""):
        """Send an email with the chat history and user details."""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"🚨 Emergency Assistance Required: {emergency_type}"
            message["From"] = f"Disaster Management Assistant <{self.sender_email}>"
            message["To"] = recipient_email
            message["Reply-To"] = user_email
            
            # Create HTML content
            html_content = self.create_email_content(
                chat_history, 
                emergency_type, 
                user_name, 
                phone_number, 
                location,
                user_email
            )
            
            # Create plain text version as fallback
            plain_text = f"""
Emergency Assistance Request
---------------------------
Time: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
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
            
            # Attach parts into message container
            part1 = MIMEText(plain_text, 'plain')
            part2 = MIMEText(html_content, 'html')
            message.attach(part1)
            message.attach(part2)
            
            # Create a secure SSL context
            context = ssl.create_default_context()
            
            # Connect to server and send email
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls(context=context)
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            return True, None
        except Exception as e:
            return False, str(e)


# Dictionary mapping emergency types to authority email addresses
EMERGENCY_AUTHORITIES = {
    "Flood": "flood.authority@example.com",
    "Earthquake": "earthquake.authority@example.com",
    "Fire": "fire.authority@example.com",
    "Medical": "medical.authority@example.com",
    "General": "general.authority@example.com"
}
