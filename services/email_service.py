"""
Email service for sending chat history to authorities.
"""
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import json

class EmailService:
    """Email service for sending chat history to authorities."""

    def __init__(self):
        """Initialize the email service with Gmail SMTP settings."""
        self.smtp_server = "smtp.gmail.com"
        self.port = 587
        self.sender_email = os.environ.get("EMAIL_USER", "themusicking151@gmail.com")
        self.password = os.environ.get("EMAIL_PASSWORD", "xoqz qqkf wkqm ycgc")

    def format_chat_history(self, messages):
        """Format chat history for email."""
        formatted_history = []
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "user":
                formatted_history.append(f"<p><strong>User:</strong> {content}</p>")
            elif role == "assistant":
                formatted_history.append(f"<p><strong>Assistant:</strong> {content}</p>")
        
        return "".join(formatted_history)

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
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # HTML content
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    border-left: 5px solid #ff4b4b;
                }}
                .chat-history {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .user-info {{
                    margin-bottom: 20px;
                }}
                .user-info p {{
                    margin: 5px 0;
                }}
                h2 {{
                    color: #ff4b4b;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Emergency Assistance Request: {emergency_type}</h2>
                <p>This conversation was shared on {current_time}</p>
            </div>
            
            <div class="user-info">
                <h3>User Information</h3>
                <p><strong>Name:</strong> {user_name or "Not provided"}</p>
                <p><strong>Phone:</strong> {phone_number or "Not provided"}</p>
                <p><strong>Email:</strong> {user_email}</p>
                <p><strong>Location:</strong> {clean_location}</p>
            </div>
            
            <div class="chat-history">
                <h3>Chat History</h3>
                {formatted_history}
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
            message["Subject"] = f"Emergency Assistance Request: {emergency_type}"
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # Create HTML content
            html_content = self.create_email_content(
                chat_history, 
                emergency_type, 
                user_name, 
                phone_number, 
                location,
                user_email
            )
            
            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)
            
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
