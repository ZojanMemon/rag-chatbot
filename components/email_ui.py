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
    
    # User contact information section with language-specific labels
    if current_language == "Urdu":
        user_info_title = "رابطہ کی معلومات"
        name_label = "آپ کا نام"
        phone_label = "فون نمبر"
        location_label = "مقام"
    elif current_language == "Sindhi":
        user_info_title = "رابطي جي معلومات"
        name_label = "توهان جو نالو"
        phone_label = "فون نمبر"
        location_label = "مڪان"
    else:  # English
        user_info_title = "Contact Information"
        name_label = "Your Name"
        phone_label = "Phone Number"
        location_label = "Location"
    
    st.markdown(f"#### {user_info_title}")
    
    # User information inputs
    col1, col2 = st.columns(2)
    with col1:
        user_name = st.text_input(name_label, key="user_name_input")
        location = st.text_input(location_label, key="user_location_input")
    with col2:
        phone_number = st.text_input(phone_label, key="user_phone_input")
    
    # Emergency type selection
    st.markdown("#### " + ("ایمرجنسی کی قسم" if current_language == "Urdu" else 
                         "ايمرجنسي جو قسم" if current_language == "Sindhi" else 
                         "Emergency Type"))
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Select box label based on language
        select_label = "Select Emergency Type"
        if current_language == "Urdu":
            select_label = "ایمرجنسی کی قسم منتخب کریں"
        elif current_language == "Sindhi":
            select_label = "ايمرجنسي جو قسم چونڊيو"
            
        selected_index = st.selectbox(
            select_label,
            options=display_options,
            key="share_emergency_type"
        )
        
        # Convert display label back to key
        selected_index_position = display_options.index(selected_index)
        emergency_type = option_keys[selected_index_position]
    
    with col2:
        # Add margin-top to the share button
        st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
        if st.button(share_button_text, type="primary", use_container_width=True):
            email_service = EmailService()
            success, _ = email_service.send_email(
                recipient_email=emergency_types[emergency_type],
                chat_history=messages,
                user_email=user_email,
                emergency_type=emergency_type,
                user_name=user_name,
                phone_number=phone_number,
                location=location
            )
            
            if success:
                st.success(success_message.format(emergency_labels[emergency_type]))
            else:
                st.error(error_message)
