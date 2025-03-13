"""Location picker component with Google Maps integration."""
import streamlit as st
import requests
import json
from typing import Optional, Tuple

def get_user_location() -> Optional[Tuple[float, float]]:
    """Get user's location using browser's geolocation API."""
    # Create a container for the location status
    status_container = st.empty()
    
    # Check if location is already in session state
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None
    
    if st.session_state.user_location is None:
        # Use JavaScript to get user location
        status_container.info("📍 Detecting your location...")
        get_location_js = """
        <script>
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    window.parent.postMessage({
                        type: 'location',
                        lat: lat,
                        lon: lon
                    }, '*');
                },
                function(error) {
                    window.parent.postMessage({
                        type: 'location_error',
                        message: error.message
                    }, '*');
                }
            );
        } else {
            window.parent.postMessage({
                type: 'location_error',
                message: 'Geolocation is not supported by this browser.'
            }, '*');
        }
        </script>
        """
        st.components.v1.html(get_location_js, height=0)
        
        # Handle the location data using Streamlit events
        if st.session_state.get('location_received'):
            lat = st.session_state.get('latitude')
            lon = st.session_state.get('longitude')
            if lat and lon:
                st.session_state.user_location = (lat, lon)
                status_container.success("📍 Location detected!")
                return lat, lon
            else:
                status_container.error("❌ Could not detect location")
                return None
    
    return st.session_state.user_location

def get_location_name(lat: float, lon: float) -> str:
    """Get location name from coordinates using Nominatim API."""
    try:
        # Use OpenStreetMap's Nominatim service (free, no API key required)
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {'User-Agent': 'DisasterManagementBot/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        
        # Extract relevant address components
        address = data.get('address', {})
        components = []
        
        # Add components in order of specificity
        if address.get('road'):
            components.append(address['road'])
        if address.get('suburb'):
            components.append(address['suburb'])
        if address.get('city'):
            components.append(address['city'])
        elif address.get('town'):
            components.append(address['town'])
        if address.get('state'):
            components.append(address['state'])
        if address.get('country'):
            components.append(address['country'])
        
        # Join components with commas
        return ', '.join(components)
    except Exception as e:
        print(f"Error getting location name: {str(e)}")
        return f"({lat}, {lon})"

def show_location_picker(current_language: str = "English") -> Optional[str]:
    """Show location picker with auto-detect and map selection options."""
    # Translations for UI elements
    if current_language == "Urdu":
        auto_detect_text = "📍 مقام کا خود بخود پتہ لگائیں"
        map_select_text = "🗺️ نقشے سے مقام منتخب کریں"
        detecting_text = "📍 مقام کا پتہ لگایا جا رہا ہے..."
        detected_text = "📍 مقام کا پتہ چل گیا"
        error_text = "❌ مقام کا پتہ نہیں چل سکا"
    elif current_language == "Sindhi":
        auto_detect_text = "📍 مڪان جو پاڻ سڃاڻپ ڪريو"
        map_select_text = "🗺️ نقشي مان مڪان چونڊيو"
        detecting_text = "📍 مڪان جي سڃاڻپ ڪري رهيو آهي..."
        detected_text = "📍 مڪان سڃاتو ويو"
        error_text = "❌ مڪان سڃاڻي نه سگهيو"
    else:  # English
        auto_detect_text = "📍 Auto-detect Location"
        map_select_text = "🗺️ Select on Map"
        detecting_text = "📍 Detecting location..."
        detected_text = "📍 Location detected"
        error_text = "❌ Could not detect location"
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(auto_detect_text, use_container_width=True):
            coords = get_user_location()
            if coords:
                lat, lon = coords
                location_name = get_location_name(lat, lon)
                st.session_state.selected_location = location_name
                return location_name
    
    with col2:
        if st.button(map_select_text, use_container_width=True):
            # Show map for location selection
            if 'selected_location' not in st.session_state:
                st.session_state.selected_location = None
                
            # Default to a central location if no location detected
            default_location = st.session_state.get('user_location', (0, 0))
            
            # Create the map using Streamlit's map component
            st.map(data=None, zoom=2)
            st.info("🗺️ Click on the map to select your location")
            
            # Handle map click events
            if st.session_state.get('map_clicked'):
                lat = st.session_state.get('map_lat')
                lon = st.session_state.get('map_lon')
                if lat and lon:
                    location_name = get_location_name(lat, lon)
                    st.session_state.selected_location = location_name
                    return location_name
    
    # Return currently selected location if any
    return st.session_state.get('selected_location')
