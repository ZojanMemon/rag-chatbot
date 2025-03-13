"""Location picker component with OpenStreetMap integration."""
import streamlit as st
import requests
from typing import Optional, Tuple
from streamlit.components.v1 import html

def get_map_html(current_language: str = "English") -> str:
    """Generate HTML for OpenStreetMap component with search."""
    # Translations
    if current_language == "Urdu":
        search_placeholder = "مقام تلاش کریں..."
        auto_detect_text = "موجودہ مقام کا پتہ لگائیں"
        confirm_text = "اس مقام کی تصدیق کریں"
    elif current_language == "Sindhi":
        search_placeholder = "مڪان ڳوليو..."
        auto_detect_text = "موجود مڪان جو پتو لڳايو"
        confirm_text = "هن مڪان جي تصديق ڪريو"
    else:  # English
        search_placeholder = "Search for a location..."
        auto_detect_text = "Detect Current Location"
        confirm_text = "Confirm Location"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Location Picker</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <style>
            #map {{
                height: 400px;
                width: 100%;
                margin-bottom: 10px;
                border-radius: 8px;
            }}
            .controls {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
            }}
            button {{
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
            }}
            .primary {{
                background-color: #FF4B4B;
                color: white;
            }}
            .secondary {{
                background-color: #f0f2f6;
                color: #262730;
            }}
            .hidden {{
                display: none;
            }}
            #preview {{
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 4px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="preview" style="min-height: 20px;"></div>
        <div class="controls">
            <button class="secondary" onclick="detectLocation()">{auto_detect_text}</button>
            <button id="confirm-btn" class="primary hidden" onclick="confirmLocation()">{confirm_text}</button>
        </div>

        <script>
        let map;
        let marker;
        let selectedLocation;
        let confirmedLocation;

        function initMap() {{
            const defaultLocation = [30.3753, 69.3451];

            // Initialize map
            map = L.map('map').setView(defaultLocation, 6);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            // Add search control
            const geocoder = L.Control.geocoder({{
                defaultMarkGeocode: false,
                placeholder: "{search_placeholder}",
                collapsed: false
            }}).addTo(map);

            geocoder.on('markgeocode', function(e) {{
                const location = e.geocode.center;
                updateMarker([location.lat, location.lng]);
                map.setView(location, 17);
            }});

            // Add marker
            marker = L.marker(defaultLocation, {{
                draggable: true
            }}).addTo(map);

            // Handle marker drag
            marker.on('dragend', function(e) {{
                const pos = e.target.getLatLng();
                updateLocationPreview([pos.lat, pos.lng]);
            }});

            // Handle map click
            map.on('click', function(e) {{
                updateMarker([e.latlng.lat, e.latlng.lng]);
            }});
        }}

        function updateMarker(latlng) {{
            marker.setLatLng(latlng);
            updateLocationPreview(latlng);
        }}

        function detectLocation() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    function(position) {{
                        const pos = [position.coords.latitude, position.coords.longitude];
                        map.setView(pos, 17);
                        updateMarker(pos);
                    }},
                    function() {{
                        alert('Error: Could not detect location.');
                    }}
                );
            }} else {{
                alert('Error: Geolocation is not supported by your browser.');
            }}
        }}

        function updateLocationPreview(latlng) {{
            selectedLocation = latlng;
            confirmedLocation = null;
            // Use Nominatim for reverse geocoding
            fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                .then(response => response.json())
                .then(data => {{
                    if (data.display_name) {{
                        const address = data.display_name;
                        document.getElementById('preview').innerHTML = `📍 ${{address}}`;
                        document.getElementById('confirm-btn').classList.remove('hidden');
                        // Clear any existing confirmation
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: null
                        }}, '*');
                    }}
                }});
        }}

        function confirmLocation() {{
            if (selectedLocation) {{
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{selectedLocation[0]}}&lon=${{selectedLocation[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name) {{
                            const address = data.display_name;
                            confirmedLocation = address;
                            // Update Streamlit with confirmed location
                            window.parent.postMessage({{
                                type: 'streamlit:setComponentValue',
                                value: `✅ ${{address}}`
                            }}, '*');
                            // Update UI
                            document.getElementById('preview').innerHTML = `✅ ${{address}}`;
                            document.getElementById('confirm-btn').classList.add('hidden');
                            
                            // Also try to directly set the session state
                            try {{
                                if (window.parent.streamlitPythonSetSessionState) {{
                                    window.parent.streamlitPythonSetSessionState('confirmed_address', address);
                                    console.log("Directly set session state to:", address);
                                }}
                            }} catch(e) {{
                                console.error("Error setting session state:", e);
                            }}
                        }}
                    }});
            }}
        }}

        // Initialize the map
        initMap();

        // If there's a location in session state, show it as confirmed
        if (window.parent.streamlitPythonGetSessionState) {{
            const location = window.parent.streamlitPythonGetSessionState('confirmed_address');
            if (location) {{
                confirmedLocation = location;
                document.getElementById('preview').innerHTML = `✅ ${{location}}`;
                document.getElementById('confirm-btn').classList.add('hidden');
            }}
        }}
        </script>
    </body>
    </html>
    """

def show_location_picker(current_language: str = "English") -> Optional[str]:
    """Show location picker with OpenStreetMap integration."""
    # Initialize session state for location if not present
    if 'confirmed_address' not in st.session_state:
        st.session_state.confirmed_address = ""
    
    # Debug the current session state
    st.write("DEBUG - Before map: confirmed_address =", repr(st.session_state.confirmed_address))

    # Show map component
    component_value = html(get_map_html(current_language), height=500)
    
    # Debug the component value
    st.write("DEBUG - Component returned:", repr(component_value))
    
    # If we got a value from the component, update the session state
    if component_value and isinstance(component_value, str):
        # Check if it's a confirmed location (starts with ✅)
        if component_value.startswith("✅ "):
            # Extract the address (remove the ✅ prefix)
            clean_address = component_value[2:].strip()
            # Store in session state
            st.session_state.confirmed_address = clean_address
            st.write("DEBUG - Updated confirmed_address =", repr(clean_address))
    
    # Return the raw component value (which may include emoji prefixes)
    return component_value
