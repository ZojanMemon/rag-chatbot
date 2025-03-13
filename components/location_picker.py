"""Location picker component with Google Maps integration."""
import streamlit as st
import requests
import json
from typing import Optional, Tuple
import folium
from streamlit_folium import folium_static

def get_user_location() -> Optional[Tuple[float, float]]:
    """Get user's location using browser's geolocation API."""
    # Create a container for the location status
    status_container = st.empty()
    
    # Initialize session state for location data
    if 'location_data' not in st.session_state:
        st.session_state.location_data = None
        
    # Add JavaScript to handle location
    location_js = """
    <script>
    if ("geolocation" in navigator) {
        console.log("Requesting location...");
        navigator.geolocation.getCurrentPosition(
            function(position) {
                console.log("Location received:", position);
                const data = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude
                };
                window.parent.postMessage(
                    {
                        type: "streamlit:set_location",
                        data: data
                    },
                    "*"
                );
            },
            function(error) {
                console.error("Location error:", error);
                window.parent.postMessage(
                    {
                        type: "streamlit:location_error",
                        data: error.message
                    },
                    "*"
                );
            }
        );
    } else {
        console.error("Geolocation not available");
    }
    </script>
    """
    
    # Only inject the JavaScript if we haven't received location data yet
    if not st.session_state.location_data:
        st.components.v1.html(location_js, height=0)
        status_container.info("📍 Detecting your location...")
        
        # Check for location data in session state (set by JavaScript)
        if 'LOCATION_DATA' in st.session_state:
            data = st.session_state.LOCATION_DATA
            if isinstance(data, dict) and 'lat' in data and 'lon' in data:
                st.session_state.location_data = (data['lat'], data['lon'])
                status_container.success("📍 Location detected!")
                return st.session_state.location_data
            
        return None
        
    return st.session_state.location_data

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
        confirm_text = "اس مقام کی تصدیق کریں"
        location_text = "منتخب کردہ مقام"
    elif current_language == "Sindhi":
        auto_detect_text = "📍 مڪان جو پاڻ سڃاڻپ ڪريو"
        map_select_text = "🗺️ نقشي مان مڪان چونڊيو"
        confirm_text = "هن مڪان جي تصديق ڪريو"
        location_text = "چونڊيل مڪان"
    else:  # English
        auto_detect_text = "📍 Auto-detect Location"
        map_select_text = "🗺️ Select on Map"
        confirm_text = "Confirm this location"
        location_text = "Selected Location"
    
    # Initialize session state
    if 'map_location' not in st.session_state:
        st.session_state.map_location = None
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = None
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(auto_detect_text, use_container_width=True):
            coords = get_user_location()
            if coords:
                lat, lon = coords
                location_name = get_location_name(lat, lon)
                st.session_state.selected_location = location_name
                st.session_state.map_location = (lat, lon)
                st.rerun()
    
    with col2:
        if st.button(map_select_text, use_container_width=True):
            st.session_state.show_map = True
            st.rerun()
    
    # Show map for location selection
    if st.session_state.get('show_map', False):
        # Get default center location
        if st.session_state.map_location:
            center = st.session_state.map_location
        else:
            # Default to a central location
            center = (30.3753, 69.3451)  # Center of Pakistan
        
        # Create a Folium map
        m = folium.Map(location=center, zoom_start=6)
        
        # Add click event handler
        m.add_child(folium.LatLngPopup())
        
        # Display the map
        map_data = folium_static(m, width=700)
        
        # Handle map click
        if 'last_clicked' in st.session_state:
            lat, lon = st.session_state.last_clicked
            location_name = get_location_name(lat, lon)
            
            st.markdown(f"#### {location_text}")
            st.info(f"📍 {location_name}")
            
            if st.button(confirm_text, type="primary"):
                st.session_state.selected_location = location_name
                st.session_state.show_map = False
                st.rerun()
            
    # Show currently selected location if any
    if st.session_state.get('selected_location'):
        st.success(f"📍 {st.session_state.selected_location}")
    
    return st.session_state.get('selected_location')
