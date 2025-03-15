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
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Location Picker</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
            #map {{
                height: 500px;
                width: 100%;
                margin-bottom: 10px;
                border-radius: 8px;
                z-index: 0;
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
            .leaflet-control-geocoder {{
                clear: both;
                margin-top: 10px;
                width: 100%;
                max-width: none;
                border-radius: 4px;
                box-shadow: 0 1px 5px rgba(0,0,0,0.4);
            }}
            .leaflet-control-geocoder-form input {{
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ccc;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="preview" style="min-height: 20px;"></div>
        <div class="controls">
            <button class="secondary" onclick="detectLocation()">{auto_detect_text}</button>
            <button id="confirm-btn" class="primary" onclick="confirmLocation()">{confirm_text}</button>
        </div>

        <script>
        let map;
        let marker;
        let selectedLocation;
        let confirmedLocation;

        // Wait for the DOM to be fully loaded
        document.addEventListener('DOMContentLoaded', function() {{
            initMap();
        }});

        function initMap() {{
            try {{
                const defaultLocation = [30.3753, 69.3451]; // Pakistan center

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
                    collapsed: false,
                    position: 'topright'
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

                // Check for previously confirmed location
                const savedAddress = localStorage.getItem('confirmedAddress');
                if (savedAddress) {{
                    document.getElementById('preview').innerHTML = `✅ ${{savedAddress}}`;
                }}

                // Force a map resize after a short delay to ensure it renders properly
                setTimeout(function() {{
                    map.invalidateSize();
                }}, 100);
            }} catch (error) {{
                console.error("Error initializing map:", error);
                document.getElementById('map').innerHTML = "Error loading map. Please refresh the page.";
            }}
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
                    function(error) {{
                        console.error("Geolocation error:", error);
                        alert('Error: Could not detect location. ' + error.message);
                    }},
                    {{
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }}
                );
            }} else {{
                alert('Error: Geolocation is not supported by your browser.');
            }}
        }}

        function updateLocationPreview(latlng) {{
            selectedLocation = latlng;
            // Use Nominatim for reverse geocoding
            fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                .then(response => response.json())
                .then(data => {{
                    if (data.display_name) {{
                        const address = data.display_name;
                        document.getElementById('preview').innerHTML = `📍 ${{address}}`;
                        
                        // Send the selected address to Streamlit
                        window.parent.postMessage({{
                            type: 'selectedAddress',
                            address: address
                        }}, '*');
                    }}
                }})
                .catch(error => {{
                    console.error("Error in reverse geocoding:", error);
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
                            
                            // Send the confirmed address to Streamlit
                            window.parent.postMessage({{
                                type: 'confirmedAddress',
                                address: address
                            }}, '*');
                        }}
                    }})
                    .catch(error => {{
                        console.error("Error confirming location:", error);
                    }});
            }}
        }}

        // Initialize the map immediately
        initMap();
        
        // Also add a window.onload handler as a backup
        window.onload = function() {{
            // Force a map resize after a short delay to ensure it renders properly
            setTimeout(function() {{
                if (map) map.invalidateSize();
            }}, 500);
        }};
        </script>
    </body>
    </html>
    """

def show_location_picker(current_language: str = "English") -> None:
    """Show location picker with OpenStreetMap integration."""
    # Initialize session state for confirmed address if not exists
    if "confirmed_address" not in st.session_state:
        st.session_state.confirmed_address = ""
    
    # Display the map component with increased height
    html(get_map_html(current_language), height=550)
    
    # Add a separate button to manually confirm the location
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Pre-fill with any address from the map if available
        address = st.text_input(
            "Confirm your address", 
            key="manual_address_input",
            help="Enter your address or use the map above to select a location"
        )
    
    with col2:
        # Add some vertical spacing to align with the text input
        st.write("")
        if st.button("Confirm Address", type="primary"):
            if address:
                st.session_state.confirmed_address = address
                st.success(f"✅ Location confirmed: {address}")
            else:
                st.error("Please enter an address")
    
    # Display the confirmed address if available
    if st.session_state.confirmed_address:
        st.info(f"📍 Confirmed location: {st.session_state.confirmed_address}")
    
    # Return the confirmed address from session state
    return st.session_state.get("confirmed_address", "")
