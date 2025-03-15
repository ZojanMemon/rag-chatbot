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
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
            }}
            #map-container {{
                position: relative;
                height: 400px;
                width: 100%;
            }}
            #map {{
                height: 100%;
                width: 100%;
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
            #preview {{
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 4px;
                font-size: 14px;
                min-height: 20px;
            }}
        </style>
    </head>
    <body>
        <div id="map-container">
            <div id="map"></div>
        </div>
        <div id="preview"></div>
        <div class="controls">
            <button class="secondary" id="detect-btn" onclick="detectLocation()">{auto_detect_text}</button>
            <button class="primary" id="confirm-btn" onclick="confirmLocation()">{confirm_text}</button>
        </div>

        <script>
            // Initialize variables
            var map, marker, selectedLocation;
            
            // Initialize map when the page loads
            window.onload = function() {{
                initMap();
            }};
            
            function initMap() {{
                // Default location (center of Pakistan)
                var defaultLocation = [30.3753, 69.3451];
                
                // Create map
                map = L.map('map').setView(defaultLocation, 5);
                
                // Add tile layer
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                
                // Add geocoder control
                var geocoder = L.Control.geocoder({{
                    defaultMarkGeocode: false,
                    placeholder: '{search_placeholder}',
                    collapsed: false
                }}).addTo(map);
                
                geocoder.on('markgeocode', function(e) {{
                    var location = e.geocode.center;
                    updateMarker([location.lat, location.lng]);
                    map.setView([location.lat, location.lng], 15);
                }});
                
                // Add marker
                marker = L.marker(defaultLocation, {{
                    draggable: true
                }}).addTo(map);
                
                // Handle marker drag
                marker.on('dragend', function(e) {{
                    var pos = e.target.getLatLng();
                    updateLocationPreview([pos.lat, pos.lng]);
                }});
                
                // Handle map click
                map.on('click', function(e) {{
                    updateMarker([e.latlng.lat, e.latlng.lng]);
                }});
                
                // Check for previously confirmed location
                var savedAddress = localStorage.getItem('confirmedAddress');
                if (savedAddress) {{
                    document.getElementById('preview').innerHTML = `✅ ${{savedAddress}}`;
                }}
                
                // Force map to resize after a delay
                setTimeout(function() {{
                    map.invalidateSize();
                }}, 200);
            }}
            
            function updateMarker(latlng) {{
                marker.setLatLng(latlng);
                updateLocationPreview(latlng);
            }}
            
            function detectLocation() {{
                if (navigator.geolocation) {{
                    document.getElementById('detect-btn').disabled = true;
                    document.getElementById('detect-btn').innerHTML = "Detecting...";
                    
                    navigator.geolocation.getCurrentPosition(
                        function(position) {{
                            var pos = [position.coords.latitude, position.coords.longitude];
                            map.setView(pos, 15);
                            updateMarker(pos);
                            
                            document.getElementById('detect-btn').disabled = false;
                            document.getElementById('detect-btn').innerHTML = "{auto_detect_text}";
                        }},
                        function(error) {{
                            console.error("Geolocation error:", error);
                            alert('Error: Could not detect location. ' + error.message);
                            
                            document.getElementById('detect-btn').disabled = false;
                            document.getElementById('detect-btn').innerHTML = "{auto_detect_text}";
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
                document.getElementById('preview').innerHTML = "Loading address...";
                
                // Use Nominatim for reverse geocoding
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name) {{
                            var address = data.display_name;
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
                        document.getElementById('preview').innerHTML = "Error loading address.";
                    }});
            }}
            
            function confirmLocation() {{
                if (selectedLocation) {{
                    document.getElementById('confirm-btn').disabled = true;
                    document.getElementById('confirm-btn').innerHTML = "Confirming...";
                    
                    fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{selectedLocation[0]}}&lon=${{selectedLocation[1]}}&format=json`)
                        .then(response => response.json())
                        .then(data => {{
                            if (data.display_name) {{
                                var address = data.display_name;
                                
                                // Store the address in localStorage
                                localStorage.setItem('confirmedAddress', address);
                                
                                // Update UI
                                document.getElementById('preview').innerHTML = `✅ ${{address}}`;
                                
                                // Send the confirmed address to Streamlit
                                window.parent.postMessage({{
                                    type: 'confirmedAddress',
                                    address: address
                                }}, '*');
                                
                                document.getElementById('confirm-btn').disabled = false;
                                document.getElementById('confirm-btn').innerHTML = "{confirm_text}";
                            }}
                        }})
                        .catch(error => {{
                            console.error("Error confirming location:", error);
                            document.getElementById('preview').innerHTML = "Error confirming location.";
                            
                            document.getElementById('confirm-btn').disabled = false;
                            document.getElementById('confirm-btn').innerHTML = "{confirm_text}";
                        }});
                }} else {{
                    alert('Please select a location first.');
                }}
            }}
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
