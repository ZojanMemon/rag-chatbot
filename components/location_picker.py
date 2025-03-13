"""Location picker component with interactive map and auto-detection."""
import streamlit as st
import requests
import pydeck as pdk
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
        auto_detect_label = " اپنی موجودہ لوکیشن کا پتہ لگائیں"
        location_label = "مقام"
        detecting_label = "لوکیشن کا پتہ لگایا جا رہا ہے..."
        map_help = "نقشے پر کلک کر کے اپنی لوکیشن منتخب کریں"
    elif current_language == "Sindhi":
        auto_detect_label = " پنهنجي موجوده مڪان جو پتو لڳايو"
        location_label = "مڪان"
        detecting_label = "مڪان جو پتو لڳايو پيو وڃي..."
        map_help = "نقشي تي ڪلڪ ڪري پنهنجي مڪان چونڊيو"
    else:  # English
        auto_detect_label = " Detect My Location"
        location_label = "Location"
        detecting_label = "Detecting location..."
        map_help = "Click on the map to select your location"

    # Initialize session state variables
    if 'location_lat' not in st.session_state:
        st.session_state.location_lat = 30.3753  # Default to Pakistan's center
    if 'location_lng' not in st.session_state:
        st.session_state.location_lng = 69.3451
    if 'location_address' not in st.session_state:
        st.session_state.location_address = ''
    if 'location_zoom' not in st.session_state:
        st.session_state.location_zoom = 5

    # Container for location input
    location_container = st.container()
    
    with location_container:
        # Location input with map toggle
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.text_input(location_label, 
                         value=st.session_state.location_address,
                         key="location_input",
                         disabled=True)
        
        with col2:
            if st.button(auto_detect_label, key="detect_location"):
                with st.spinner(detecting_label):
                    loc = get_geolocation()
                    if loc and 'coords' in loc:
                        lat = loc['coords']['latitude']
                        lng = loc['coords']['longitude']
                        address = get_address_from_coords(lat, lng)
                        if address:
                            st.session_state.location_address = address
                            st.session_state.location_lat = lat
                            st.session_state.location_lng = lng
                            st.session_state.location_zoom = 13
                            st.rerun()

        # Show interactive map
        st.caption(map_help)

        # Create map layer with marker
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=[{
                "position": [
                    st.session_state.location_lng,
                    st.session_state.location_lat
                ],
                "size": 100
            }],
            get_position="position",
            get_radius=30,
            get_fill_color=[255, 0, 0, 140],
            pickable=True
        )

        # Create view state
        view_state = pdk.ViewState(
            longitude=st.session_state.location_lng,
            latitude=st.session_state.location_lat,
            zoom=st.session_state.location_zoom,
            min_zoom=4,
            max_zoom=20,
            pitch=0,
            bearing=0
        )

        # Create the deck
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style=pdk.map_styles.ROAD,
            tooltip={"text": "Click anywhere to select location"},
            height=400
        )

        # Show the map and get click events
        st.pydeck_chart(r)

        # Handle map clicks
        if st._get_last_map_click() is not None:
            try:
                lng, lat = st._get_last_map_click()
                address = get_address_from_coords(lat, lng)
                if address:
                    st.session_state.location_address = address
                    st.session_state.location_lat = lat
                    st.session_state.location_lng = lng
                    st.session_state.location_zoom = 13
                    st.rerun()
            except Exception:
                pass

    return st.session_state.location_address
