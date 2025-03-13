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
                height: 300px;
                width: 100%;
                margin-bottom: 10px;
                border-radius: 8px;
            }}
            .controls {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
                position: sticky;
                bottom: 0;
                background: white;
                padding: 10px 0;
                z-index: 1000;
            }}
            button {{
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                width: 100%;
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
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 4px;
                font-size: 14px;
                max-height: 80px;
                overflow-y: auto;
                word-break: break-word;
                min-height: 0;
                display: none;
            }}
            #preview:not(:empty) {{
                display: block;
                margin: 10px 0;
            }}
            @media (max-width: 480px) {{
                #map {{
                    height: 250px;
                    margin-bottom: 5px;
                }}
                .controls {{
                    flex-direction: column;
                    gap: 8px;
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    padding: 10px;
                    box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
                }}
                button {{
                    margin: 0;
                }}
                #preview:not(:empty) {{
                    margin-bottom: 80px;
                }}
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="preview"></div>
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
                            
                            // Store the address in localStorage
                            localStorage.setItem('confirmedAddress', address);
                            
                            // Update UI
                            document.getElementById('preview').innerHTML = `✅ ${{address}}`;
                            document.getElementById('confirm-btn').classList.add('hidden');
                        }}
                    }});
            }}
        }}

        // Initialize the map
        initMap();
        </script>
    </body>
    </html>
    """

def show_location_picker(current_language: str = "English") -> None:
    """Show location picker with OpenStreetMap integration."""
    # Display the map component
    html(get_map_html(current_language), height=600)
    
    # Add a separate button to manually confirm the location
    col1, col2 = st.columns([3, 1])
    
    with col1:
        address = st.text_input("Confirm your address", key="manual_address_input")
    
    with col2:
        if st.button("Confirm Address", type="primary"):
            if address:
                st.session_state["confirmed_location"] = f"✅ {address}"
                st.rerun()
    
    # Return the confirmed address from session state
    return st.session_state.get("confirmed_location", "")
