"""Email sharing component for the chatbot."""
import streamlit as st
from services.email_service import EmailService

def show_email_ui(messages, user_email="Anonymous"):
    """Display the email sharing interface."""
    # Only show after some conversation
    if len(messages) < 2:
        return

    # Get current language from session state
    current_language = st.session_state.get("output_language", "English")
    
    # Separator
    st.markdown("---")
    
    # Email sharing section with language-specific labels
    if current_language == "Urdu":
        st.markdown("### 📧 حکام کے ساتھ شیئر کریں")
        st.info("فوری مدد کے لیے یہ گفتگو متعلقہ حکام کے ساتھ شیئر کریں۔")
        share_button_text = "📤 شیئر کریں"
        success_message = "✅ {} حکام کے ساتھ شیئر کیا گیا"
        error_message = "❌ گفتگو شیئر نہیں کی جا سکی"
    elif current_language == "Sindhi":
        st.markdown("### 📧 اختيارن سان شيئر ڪريو")
        st.info("فوري مدد لاءِ هي ڳالهه ٻولهه متعلقه اختيارن سان شيئر ڪريو.")
        share_button_text = "📤 شيئر ڪريو"
        success_message = "✅ {} اختيارن سان شيئر ٿي ويو"
        error_message = "❌ ڳالهه ٻولهه شيئر نه ٿي سگهي"
    else:  # English
        st.markdown("### 📧 Share with Authorities")
        st.info("Share this conversation with relevant authorities for immediate assistance.")
        share_button_text = "📤 Share"
        success_message = "✅ Shared with {} authorities"
        error_message = "❌ Could not share the conversation"
    
    # Emergency type selection
    emergency_types = {
        "Flood": "themusicking151@gmail.com",
        "Earthquake": "themusicking151@gmail.com",
        "Fire": "themusicking151@gmail.com",
        "Medical": "themusicking151@gmail.com",
        "General": "themusicking151@gmail.com"
    }
    
    # Emergency type labels based on language
    if current_language == "Urdu":
        emergency_labels = {
            "Flood": "سیلاب",
            "Earthquake": "زلزلہ",
            "Fire": "آگ",
            "Medical": "طبی",
            "General": "عام"
        }
    elif current_language == "Sindhi":
        emergency_labels = {
            "Flood": "ٻوڏ",
            "Earthquake": "زلزلو",
            "Fire": "باهه",
            "Medical": "طبي",
            "General": "عام"
        }
    else:  # English
        emergency_labels = {
            "Flood": "Flood",
            "Earthquake": "Earthquake",
            "Fire": "Fire",
            "Medical": "Medical",
            "General": "General"
        }
    
    # Create display options with translated labels but keep keys the same
    display_options = [emergency_labels[key] for key in emergency_types.keys()]
    option_keys = list(emergency_types.keys())
    
    # Create a more structured layout to ensure consistent alignment
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Select box label based on language
        select_label = "Select Emergency Type"
        if current_language == "Urdu":
            select_label = "ایمرجنسی کی قسم منتخب کریں"
        elif current_language == "Sindhi":
            select_label = "ايمرجنسي جو قسم چونڊيو"
        
        # Add the label separately to control spacing
        st.markdown(f"**{select_label}**")
        
        # Add the selectbox without a label
        selected_index = st.selectbox(
            "",  # Empty label
            options=display_options,
            key="share_emergency_type",
            label_visibility="collapsed"  # Hide the label completely
        )
        
        # Convert display label back to key
        selected_index_position = display_options.index(selected_index)
        emergency_type = option_keys[selected_index_position]
    
    with col2:
        # Add empty space with the same height as the label
        st.markdown("&nbsp;")  # Non-breaking space for consistent height
        
        # Now the button will align with the selectbox
        if st.button(share_button_text, type="primary", use_container_width=True):
            email_service = EmailService()
            success, _ = email_service.send_email(
                recipient_email=emergency_types[emergency_type],
                chat_history=messages,
                user_email=user_email,
                emergency_type=emergency_type
            )
            
            if success:
                st.success(success_message.format(emergency_labels[emergency_type]))
            else:
                st.error(error_message)
