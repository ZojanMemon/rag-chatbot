"""Email sharing component for the chatbot."""
import streamlit as st
import time
from services.email_service import EmailService
from components.location_picker import show_location_picker

def show_email_ui(messages, user_email="Anonymous", is_emergency=False):
    """
    Display the email sharing interface.
    
    Args:
        messages: Chat history messages
        user_email: User's email address
        is_emergency: Whether this is an emergency situation (auto-expands UI)
    """
    # Only show after some conversation
    if len(messages) < 2:
        return

    # Get current language from session state
    current_language = st.session_state.get("output_language", "English")
    
    # Email sharing section with language-specific labels
    if current_language == "Urdu":
        expander_title = "📧 حکام کے ساتھ شیئر کریں"
        info_text = "فوری مدد کے لیے یہ گفتگو متعلقہ حکام کے ساتھ شیئر کریں۔"
        share_button_text = "📤 شیئر کریں"
        success_message = "✅ {} حکام کے ساتھ شیئر کیا گیا"
        error_message = "❌ گفتگو شیئر نہیں کی جا سکی"
        select_location_text = "براہ کرم مقام منتخب کریں"
        no_location_warning = "براہ کرم پہلے مقام منتخب کریں"
        emergency_help_text = "آپ ایمرجنسی میں ہیں؟ فوری مدد کے لیے اس گفتگو کو متعلقہ حکام کے ساتھ شیئر کریں۔"
        yes_immediate_help = "ہاں، مجھے فوری مدد کی ضرورت ہے"
        no_just_info = "نہیں، صرف معلومات چاہیے"
    elif current_language == "Sindhi":
        expander_title = "📧 اختيارن سان شيئر ڪريو"
        info_text = "فوري مدد لاءِ هي ڳالهه ٻولهه متعلقه اختيارن سان شيئر ڪريو."
        share_button_text = "📤 شيئر ڪريو"
        success_message = "✅ {} اختيارن سان شيئر ٿي ويو"
        error_message = "❌ ڳالهه ٻولهه شيئر نه ٿي سگهي"
        select_location_text = "مهرباني ڪري مڪان چونڊيو"
        no_location_warning = "مهرباني ڪري پهريان مڪان چونڊيو"
        emergency_help_text = "ڇا توهان ايمرجنسي ۾ آهيو؟ فوري مدد لاءِ هي ڳالهه ٻولهه متعلقه اختيارن سان شيئر ڪريو."
        yes_immediate_help = "ها، مونکي فوري مدد گهرجي"
        no_just_info = "نه، رڳو معلومات گهرجن"
    else:  # English
        expander_title = "📧 Share with Authorities"
        info_text = "Share this conversation with relevant authorities for immediate assistance."
        share_button_text = "📤 Share"
        success_message = "✅ Shared with {} authorities"
        error_message = "❌ Could not share the conversation"
        select_location_text = "Please select a location"
        no_location_warning = "Please select a location first"
        emergency_help_text = "Are you in an emergency? Share this conversation with relevant authorities for immediate help."
        yes_immediate_help = "Yes, I need immediate help"
        no_just_info = "No, just information"
        
    # Create an expander for the sharing interface - auto-expand if emergency
    with st.expander(expander_title, expanded=is_emergency):
        # If it's an emergency, show prominent emergency help text
        if is_emergency:
            st.error(emergency_help_text)
            
            # Quick action buttons for emergency confirmation
            col1, col2 = st.columns(2)
            with col1:
                emergency_confirmed = st.button(
                    yes_immediate_help, 
                    type="primary", 
                    use_container_width=True
                )
            with col2:
                emergency_denied = st.button(
                    no_just_info,
                    use_container_width=True
                )
                
            # If user confirms emergency, store in session state
            if emergency_confirmed:
                st.session_state.emergency_confirmed = True
                st.session_state.emergency_denied = False
            elif emergency_denied:
                st.session_state.emergency_confirmed = False
                st.session_state.emergency_denied = True
                
            # If emergency is confirmed, show a more prominent message
            if st.session_state.get("emergency_confirmed", False):
                st.warning("📞 Please also call emergency services if possible (15 or 1122)")
        else:
            st.info(info_text)
        
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
            user_info_title = "رابطہ کی معلومات"
            name_label = "آپ کا نام"
            phone_label = "فون نمبر"
            location_label = "مقام"
        elif current_language == "Sindhi":
            emergency_labels = {
                "Flood": "ٻوڏ",
                "Earthquake": "زلزلو",
                "Fire": "باهه",
                "Medical": "طبي",
                "General": "عام"
            }
            user_info_title = "رابطي جي معلومات"
            name_label = "توهان جو نالو"
            phone_label = "فون نمبر"
            location_label = "مڪان"
        else:  # English
            emergency_labels = {
                "Flood": "Flood",
                "Earthquake": "Earthquake",
                "Fire": "Fire",
                "Medical": "Medical",
                "General": "General"
            }
            user_info_title = "Contact Information"
            name_label = "Your Name"
            phone_label = "Phone Number"
            location_label = "Location"
        
        # Create display options with translated labels but keep keys the same
        display_options = [emergency_labels[key] for key in emergency_types.keys()]
        option_keys = list(emergency_types.keys())
        
        st.markdown(f"#### {user_info_title}")
        
        # User information inputs
        col1, col2 = st.columns(2)
        with col1:
            user_name = st.text_input(name_label, key="user_name_input")
        with col2:
            phone_number = st.text_input(phone_label, key="user_phone_input")
        
        # Initialize session state for confirmed address if not present
        if "confirmed_address" not in st.session_state:
            st.session_state.confirmed_address = ""
            
        # Location picker
        st.markdown(f"#### {location_label}")
        
        # Show the location picker
        show_location_picker(current_language)
        
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
                
            # Auto-select emergency type if we can detect it from the messages
            default_index = 0
            if is_emergency:
                last_message = messages[-1]["content"].lower() if messages else ""
                if "flood" in last_message or "water" in last_message:
                    default_index = display_options.index(emergency_labels["Flood"])
                elif "earthquake" in last_message:
                    default_index = display_options.index(emergency_labels["Earthquake"])
                elif "fire" in last_message:
                    default_index = display_options.index(emergency_labels["Fire"])
                elif "medical" in last_message or "hurt" in last_message or "injured" in last_message:
                    default_index = display_options.index(emergency_labels["Medical"])
            
            selected_index = st.selectbox(
                select_label,
                options=display_options,
                index=default_index,
                key="share_emergency_type"
            )
            
            # Convert display label back to key
            selected_index_position = display_options.index(selected_index)
            emergency_type = option_keys[selected_index_position]
        
        with col2:
            # Add margin-top to the share button
            st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
            
            # Get the confirmed address from session state
            location = st.session_state.get("confirmed_address", "")
            
            # Create a share button - make it more prominent for emergencies
            button_type = "primary" if is_emergency else "primary"
            
            if st.button(share_button_text, type=button_type, use_container_width=True, disabled=not location):
                if location:
                    # Show a spinner while sending email
                    with st.spinner("Sending..."):
                        email_service = EmailService()
                        success, error = email_service.send_email(
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
                            # Clear location after successful send
                            st.session_state.confirmed_address = ""
                        else:
                            st.error(f"{error_message}: {error}")
                else:
                    st.warning(no_location_warning)
