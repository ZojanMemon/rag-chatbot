"""Location picker component with interactive map and auto-detection."""
import streamlit as st
import requests
from streamlit_js_eval import get_geolocation

def show_location_picker(current_language: str = "English") -> str:
    """Display the location picker component with language support."""
    # Labels based on language
    if current_language == "Urdu":
        auto_detect_label = "📍 اپنی موجودہ لوکیشن کا پتہ لگائیں"
        location_label = "مقام"
        detecting_label = "لوکیشن کا پتہ لگایا جا رہا ہے..."
        map_help = "نقشے پر کلک کر کے اپنی لوکیشن منتخب کریں"
    elif current_language == "Sindhi":
        auto_detect_label = "📍 پنهنجي موجوده مڪان جو پتو لڳايو"
        location_label = "مڪان"
        detecting_label = "مڪان جو پتو لڳايو پيو وڃي..."
        map_help = "نقشي تي ڪلڪ ڪري پنهنجي مڪان چونڊيو"
    else:  # English
        auto_detect_label = "📍 Detect My Location"
        location_label = "Location"
        detecting_label = "Detecting location..."
        map_help = "Click on the map to select your location"

    # Initialize session state for location data
    if 'location_data' not in st.session_state:
        st.session_state.location_data = {
            'address': '',
            'lat': 24.8607,  # Default to Pakistan's center
            'lng': 67.0011,
            'map_initialized': False
        }

    # Container for location input
    location_container = st.container()
    
    with location_container:
        # Location input with map toggle
        col1, col2 = st.columns([3, 1])
        
        with col1:
            location = st.text_input(location_label, 
                                   value=st.session_state.location_data['address'],
                                   key="location_input")
            
            # Update address in session state when manually entered
            if location != st.session_state.location_data['address']:
                st.session_state.location_data['address'] = location
        
        with col2:
            if st.button(auto_detect_label, key="detect_location"):
                with st.spinner(detecting_label):
                    loc = get_geolocation()
                    if loc:
                        st.session_state.location_data['lat'] = loc['coords']['latitude']
                        st.session_state.location_data['lng'] = loc['coords']['longitude']
                        st.session_state.location_data['map_initialized'] = True
                        
                        # Get address from coordinates
                        try:
                            response = requests.get(
                                f"https://nominatim.openstreetmap.org/reverse?lat={loc['coords']['latitude']}&lon={loc['coords']['longitude']}&format=json"
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.location_data['address'] = data.get('display_name', '')
                                st.experimental_rerun()
                        except Exception:
                            pass

        # Show interactive map
        st.caption(map_help)
        selected_point = st.map(
            data=[{
                'lat': st.session_state.location_data['lat'],
                'lon': st.session_state.location_data['lng']
            }],
            zoom=13
        )
        
        # Update location if map is clicked
        if selected_point:
            try:
                st.session_state.location_data['lat'] = selected_point['last_clicked']['lat']
                st.session_state.location_data['lng'] = selected_point['last_clicked']['lng']
                
                # Get address for new coordinates
                response = requests.get(
                    f"https://nominatim.openstreetmap.org/reverse?lat={st.session_state.location_data['lat']}&lon={st.session_state.location_data['lng']}&format=json"
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.location_data['address'] = data.get('display_name', '')
                    st.experimental_rerun()
            except Exception:
                pass

    return st.session_state.location_data['address']
