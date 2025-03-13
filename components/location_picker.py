"""Location picker component with Google Maps integration and auto-detection."""
import streamlit as st
import json
import requests
from typing import Optional, Tuple

def get_user_location() -> Optional[Tuple[float, float]]:
    """Get user's location using the IP Geolocation API."""
    try:
        response = requests.get('https://ipapi.co/json/')
        if response.status_code == 200:
            data = response.json()
            return data.get('latitude'), data.get('longitude')
    except Exception:
        return None
    return None

def show_location_picker(current_language: str = "English") -> str:
    """Display the location picker component with language support."""
    # Labels based on language
    if current_language == "Urdu":
        auto_detect_label = "📍 اپنی موجودہ لوکیشن کا پتہ لگائیں"
        location_label = "مقام"
        map_placeholder = "نقشہ لوڈ ہو رہا ہے..."
        detecting_label = "لوکیشن کا پتہ لگایا جا رہا ہے..."
    elif current_language == "Sindhi":
        auto_detect_label = "📍 پنهنجي موجوده مڪان جو پتو لڳايو"
        location_label = "مڪان"
        map_placeholder = "نقشو لوڊ ٿي رهيو آهي..."
        detecting_label = "مڪان جو پتو لڳايو پيو وڃي..."
    else:  # English
        auto_detect_label = "📍 Detect My Location"
        location_label = "Location"
        map_placeholder = "Loading map..."
        detecting_label = "Detecting location..."

    # Container for location input
    location_container = st.container()
    
    with location_container:
        # Location input with map toggle
        col1, col2 = st.columns([3, 1])
        
        with col1:
            location = st.text_input(location_label, key="location_input")
        
        with col2:
            if st.button(auto_detect_label, key="detect_location"):
                with st.spinner(detecting_label):
                    coords = get_user_location()
                    if coords:
                        lat, lon = coords
                        # Get address from coordinates using Nominatim
                        try:
                            response = requests.get(
                                f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
                            )
                            if response.status_code == 200:
                                data = response.json()
                                address = data.get('display_name', '')
                                # Update the location input
                                st.session_state.location_input = address
                                location = address
                                # Show the map
                                st.session_state.show_map = True
                                st.session_state.map_center = [lat, lon]
                        except Exception:
                            pass

        # Show map if coordinates are available
        if st.session_state.get('show_map', False) and st.session_state.get('map_center'):
            lat, lon = st.session_state.map_center
            # Create a map using OpenStreetMap
            map_html = f"""
            <div style="width: 100%; height: 200px; margin: 10px 0; border-radius: 10px; overflow: hidden;">
                <iframe width="100%" height="100%" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"
                    src="https://www.openstreetmap.org/export/embed.html?bbox={lon-0.01}%2C{lat-0.01}%2C{lon+0.01}%2C{lat+0.01}&amp;layer=mapnik&amp;marker={lat}%2C{lon}"
                    style="border: 1px solid #ddd;">
                </iframe>
            </div>
            """
            st.markdown(map_html, unsafe_allow_html=True)

    return location
