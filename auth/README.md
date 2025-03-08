# Firebase Authentication for Disaster Management Chatbot

This module adds user authentication and chat history persistence to the Disaster Management Chatbot using Firebase.

## Features

- **User Authentication**: Secure login and registration
- **Chat History**: Save and retrieve chat conversations
- **User Preferences**: Store and sync language preferences
- **Multiple Chat Sessions**: Create and manage multiple conversations

## Setup Instructions

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" and follow the setup wizard
3. Enable Authentication (Email/Password method)
4. Create a Firestore database in test mode

### 2. Get Firebase Credentials

1. In Firebase Console, go to Project Settings
2. Navigate to "Service accounts" tab
3. Click "Generate new private key"
4. Save the JSON file securely

### 3. Set Up Environment

#### Option A: Using Streamlit Secrets (Recommended for Deployment)

1. Create a `.streamlit/secrets.toml` file with:
```toml
FIREBASE_SERVICE_ACCOUNT = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "your-private-key",
  ...rest of your service account JSON...
}
'''
```

#### Option B: Using Environment Variables (Local Development)

1. Create a `.env` file with:
```
FIREBASE_SERVICE_ACCOUNT={"type":"service_account","project_id":"your-project-id",...}
```

#### Option C: Using Service Account File

1. Save the Firebase service account JSON as `firebase-service-account.json` in the project root

### 4. Install Dependencies

```bash
pip install -r auth/requirements.txt
```

### 5. Run the App

To run the app with authentication:

```bash
streamlit run auth_app.py
```

To run the original app without authentication:

```bash
streamlit run app.py
```

## Firebase Data Structure

The authentication system uses the following Firestore structure:

```
/users/{user_id}/
  - name: string
  - email: string
  - password_hash: string (bcrypt)
  - preferences: map
    - input_language: string
    - output_language: string
    - theme: string
  - current_session_id: string
  
  /chat_sessions/{session_id}/
    - title: string
    - created_at: timestamp
    - updated_at: timestamp
    
    /messages/{message_id}/
      - role: string ("user" or "assistant")
      - content: string
      - timestamp: timestamp
      - metadata: map
        - language: string
        - type: string
```

## Integration with Existing App

The authentication system is designed to work alongside the existing app without modifying the original code. The `auth_app.py` file demonstrates how to integrate authentication while preserving all the original functionality.

## Security Considerations

- All passwords are hashed using bcrypt before storage
- Firebase Authentication handles secure token management
- Firestore security rules should be configured to restrict access to user data
- API keys and credentials are never exposed to the client
