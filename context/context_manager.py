"""Manages and formats conversation context for the chatbot."""
from typing import List, Dict

MAX_CONTEXT_MESSAGES = 10 # Limit the number of messages used for context

def format_chat_history(messages: List[Dict]) -> str:
    """
    Formats the chat history into a string suitable for the LLM prompt.

    Args:
        messages: A list of chat messages, where each message is a dictionary
                  with 'role' ('user' or 'assistant') and 'content'.

    Returns:
        A formatted string representing the recent conversation history.
    """
    # Take the last N messages, excluding the system message if any
    relevant_messages = [m for m in messages if m['role'] != 'system'][-MAX_CONTEXT_MESSAGES:]

    if not relevant_messages:
        return "No previous conversation history."

    formatted_history = "\n\nPrevious Conversation History:\n"
    for msg in relevant_messages:
        role = "Human" if msg['role'] == 'user' else "AI Assistant"
        formatted_history += f"{role}: {msg['content']}\n"

    return formatted_history.strip()
