"""Styles for question suggestions.

This module provides CSS styles for the question suggestions UI.
"""

# CSS for question suggestions
SUGGESTION_CSS = """
<style>
.suggestion-card {
    background-color: rgba(49, 51, 63, 0.2);
    border-radius: 12px;
    border: 1px solid rgba(49, 51, 63, 0.2);
    padding: 15px;
    margin-bottom: 20px;
    transition: all 0.3s ease;
}

.suggestion-card:hover {
    border-color: #4e8df5;
    background-color: rgba(78, 141, 245, 0.1);
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.suggestion-title {
    font-size: 1.1em;
    font-weight: 600;
    margin-bottom: 10px;
    color: #4e8df5;
}

.suggestion-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 20px;
}

.suggestion-button {
    background-color: rgba(49, 51, 63, 0.2);
    border-radius: 10px;
    border: 1px solid rgba(49, 51, 63, 0.2);
    color: inherit;
    padding: 12px 15px;
    cursor: pointer;
    text-align: left;
    transition: all 0.3s ease;
    width: 100%;
    font-size: 0.95em;
}

.suggestion-button:hover {
    border-color: #4e8df5;
    background-color: rgba(78, 141, 245, 0.1);
}

.suggestion-icon {
    margin-right: 8px;
    color: #4e8df5;
}
</style>
"""

# Function to inject CSS
def inject_suggestion_styles():
    """Inject CSS styles for question suggestions."""
    import streamlit as st
    st.markdown(SUGGESTION_CSS, unsafe_allow_html=True)
