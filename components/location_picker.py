"""Location picker component with interactive map and auto-detection."""
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

def get_address_from_coords(lat, lng):
    """Get address from coordinates using Nominatim."""
    try:
        response = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('display_name', '')
    except Exception:
        pass
    return ''

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
            'lat': 30.3753,  # Default to Pakistan's center
            'lng': 69.3451,
            'zoom': 5
        }

    # Container for location input
    location_container = st.container()
    
    with location_container:
        # Location input with map toggle
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text_input(location_label, 
                         value=st.session_state.location_data['address'],
                         key="location_input",
                         disabled=True)
        
        with col2:
            if st.button(auto_detect_label, key="detect_location"):
                with st.spinner(detecting_label):
                    loc = get_geolocation()
                    if loc:
                        lat = loc['coords']['latitude']
                        lng = loc['coords']['longitude']
                        address = get_address_from_coords(lat, lng)
                        
                        st.session_state.location_data.update({
                            'lat': lat,
                            'lng': lng,
                            'address': address,
                            'zoom': 13
                        })
                        st.experimental_rerun()

        # Show interactive map
        st.caption(map_help)
        
        # Create a folium map
        m = folium.Map(
            location=[st.session_state.location_data['lat'], 
                     st.session_state.location_data['lng']],
            zoom_start=st.session_state.location_data['zoom'],
            dragging=True,
            scrollWheelZoom=True
        )

        # Add a marker for current location
        folium.Marker(
            [st.session_state.location_data['lat'], 
             st.session_state.location_data['lng']],
            popup="Selected Location",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

        # Display the map
        map_data = st_folium(
            m,
            height=300,
            width="100%",
            returned_objects=["last_clicked"]
        )

        # Handle map clicks
        if map_data["last_clicked"]:
            lat = map_data["last_clicked"]["lat"]
            lng = map_data["last_clicked"]["lng"]
            address = get_address_from_coords(lat, lng)
            
            st.session_state.location_data.update({
                'lat': lat,
                'lng': lng,
                'address': address,
                'zoom': 13
            })
            st.experimental_rerun()

    return st.session_state.location_data['address']
