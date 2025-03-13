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
                background-color: #ff4b4b;
                color: white;
            }}
            .secondary {{
                background-color: #f0f2f6;
                color: #0f1629;
            }}
            .location-preview {{
                margin-top: 10px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 4px;
                font-size: 14px;
            }}
            .leaflet-control-geocoder {{
                margin-top: 10px !important;
            }}
            .leaflet-control-geocoder-form input {{
                width: 100%;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
            }}
            .hidden {{
                display: none;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="controls">
            <button onclick="detectLocation()" class="secondary">
                📍 {auto_detect_text}
            </button>
            <button onclick="confirmLocation()" class="primary hidden" id="confirm-btn">
                ✓ {confirm_text}
            </button>
        </div>
        <div id="preview" class="location-preview"></div>

        <script>
        let map;
        let marker;
        let selectedLocation = null;
        let confirmedLocation = null;

        function initMap() {{
            // Center of Pakistan
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
                                value: address
                            }}, '*');
                            // Update UI
                            document.getElementById('preview').innerHTML = `✅ ${{address}}`;
                            document.getElementById('confirm-btn').classList.add('hidden');
                        }}
                    }});
            }}
        }}

        // Initialize the map
        initMap();

        // If there's a location in session state, show it as confirmed
        if (window.parent.streamlitPythonGetSessionState) {{
            const location = window.parent.streamlitPythonGetSessionState('selected_location');
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
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = None

    # Show map component
    component_value = html(get_map_html(current_language), height=500)
    
    # Handle location selection
    if component_value is not None:
        st.session_state.selected_location = component_value
        return component_value
    
    return st.session_state.selected_location
