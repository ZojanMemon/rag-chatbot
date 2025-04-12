"""CSS styles for the question cards component.

This module contains the CSS styles for the question cards to ensure
they look beautiful and consistent with the rest of the application.
"""

# Main CSS for question cards with animations and responsive design
CARD_CSS = """
<style>
/* Question Cards Container */
.question-cards-container {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin: 20px 0 30px 0;
    justify-content: center;
    animation: fadeIn 0.5s ease-in-out;
}

/* Individual Question Card */
.question-card {
    background: linear-gradient(145deg, rgba(59, 61, 73, 0.7), rgba(49, 51, 63, 0.8));
    border-radius: 12px;
    padding: 16px;
    width: calc(50% - 15px);
    min-width: 220px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    cursor: pointer;
    border: 1px solid rgba(128, 128, 128, 0.2);
    position: relative;
    overflow: hidden;
}

/* Hover Effects */
.question-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    border-color: rgba(128, 128, 128, 0.5);
}

.question-card:hover::after {
    opacity: 1;
}

.question-card::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(45deg, transparent 65%, rgba(255, 255, 255, 0.08) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

/* Card Title */
.question-card h4 {
    margin: 0;
    font-size: 16px;
    color: #ffffff;
    font-weight: 500;
    line-height: 1.4;
}

/* Card Subtitle */
.question-card p {
    margin: 8px 0 0 0;
    font-size: 13px;
    color: #cccccc;
    display: flex;
    align-items: center;
    gap: 5px;
}

.question-card p::before {
    content: '→';
    font-size: 14px;
    color: #8c8c8c;
}

/* Welcome Header */
.welcome-header {
    text-align: center;
    margin-bottom: 25px;
    padding: 25px 20px;
    background: linear-gradient(145deg, rgba(59, 61, 73, 0.5), rgba(49, 51, 63, 0.6));
    border-radius: 15px;
    border: 1px solid rgba(128, 128, 128, 0.2);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    animation: slideDown 0.5s ease-in-out;
}

.welcome-header h2 {
    margin: 0;
    color: #ffffff;
    font-weight: 600;
    font-size: 24px;
}

.welcome-header p {
    margin: 12px 0 0 0;
    color: #cccccc;
    font-size: 16px;
    line-height: 1.5;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideDown {
    from { transform: translateY(-20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}

/* Responsive Design */
@media (max-width: 768px) {
    .question-card {
        width: 100%;
    }
    
    .welcome-header {
        padding: 20px 15px;
    }
    
    .welcome-header h2 {
        font-size: 22px;
    }
    
    .welcome-header p {
        font-size: 14px;
    }
}
</style>
"""

# Additional CSS for dark mode and accessibility
ACCESSIBILITY_CSS = """
<style>
/* Accessibility Improvements */
.question-card:focus {
    outline: 2px solid #4d8bf8;
    box-shadow: 0 0 0 4px rgba(77, 139, 248, 0.3);
}

/* High Contrast Mode */
@media (prefers-contrast: high) {
    .question-card {
        background: #2a2a2a;
        border: 2px solid #ffffff;
    }
    
    .question-card h4 {
        color: #ffffff;
    }
    
    .question-card p {
        color: #ffffff;
    }
    
    .welcome-header {
        background: #2a2a2a;
        border: 2px solid #ffffff;
    }
    
    .welcome-header h2,
    .welcome-header p {
        color: #ffffff;
    }
}
</style>
"""

def get_card_css() -> str:
    """Get the combined CSS for question cards.
    
    Returns:
        str: Complete CSS for the question cards component
    """
    return CARD_CSS + ACCESSIBILITY_CSS
