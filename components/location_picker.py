"""Location picker component with OpenStreetMap integration."""
import streamlit as st
import requests
import json
from typing import Optional, Tuple
from streamlit.components.v1 import html

def get_map_html(current_language: str = "English", key: str = "location_picker") -> str:
    """Generate HTML for OpenStreetMap component with search."""
    # Translations
    if current_language == "Urdu":
        search_placeholder = "مقام تلاش کریں..."
        auto_detect_text = "موجودہ مقام کا پتہ لگائیں"
        confirm_text = "اس مقام کی تصدیق کریں"
        dragging_text = "کھینچ رہے ہیں..."
    elif current_language == "Sindhi":
        search_placeholder = "مڪان ڳوليو..."
        auto_detect_text = "موجود مڪان جو پتو لڳايو"
        confirm_text = "هن مڪان جي تصديق ڪريو"
        dragging_text = "ڪشي رهيو آهي..."
    else:  # English
        search_placeholder = "Search for a location..."
        auto_detect_text = "Detect Current Location"
        confirm_text = "Confirm Location"
        dragging_text = "Dragging..."

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Location Picker</title>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css" />
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
            }}
            #map {{
                height: 400px;
                width: 100%;
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
            #preview {{
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 4px;
                font-size: 14px;
                min-height: 20px;
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
            .dragging {{
                background-color: #FFD700;
                color: #000;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="preview"></div>
        <div class="controls">
            <button class="secondary" id="detect-btn" onclick="detectLocation()">{auto_detect_text}</button>
            <button class="primary" id="confirm-btn" onclick="confirmLocation()">{confirm_text}</button>
        </div>

        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <script>
            var map, marker, selectedLocation;
            var defaultLocation = [30.3753, 69.3451]; // Pakistan center
            var isDragging = false;
            var debounceTimer;
            var componentKey = "{key}";
            
            // Initialize map when DOM is fully loaded
            document.addEventListener('DOMContentLoaded', function() {{
                initializeMap();
            }});
            
            function initializeMap() {{
                // Create map
                map = L.map('map').setView(defaultLocation, 5);
                
                // Add tile layer
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                
                // Create marker
                marker = L.marker(defaultLocation, {{ draggable: true }}).addTo(map);
                selectedLocation = defaultLocation;
                
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
                
                // Handle marker drag start
                marker.on('dragstart', function(e) {{
                    isDragging = true;
                    document.getElementById('preview').innerHTML = `📍 {dragging_text}`;
                    document.getElementById('preview').className = 'dragging';
                }});
                
                // Handle marker drag
                marker.on('drag', function(e) {{
                    var pos = e.target.getLatLng();
                    selectedLocation = [pos.lat, pos.lng];
                    
                    // Update coordinates in real-time
                    document.getElementById('preview').innerHTML = 
                        `📍 {dragging_text} Lat: ${{pos.lat.toFixed(6)}}, Lng: ${{pos.lng.toFixed(6)}}`;
                    
                    // Debounce the reverse geocoding during drag
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(function() {{
                        if (isDragging) {{
                            updateLocationPreviewDuringDrag([pos.lat, pos.lng]);
                        }}
                    }}, 300);
                }});
                
                // Handle marker drag end
                marker.on('dragend', function(e) {{
                    var pos = e.target.getLatLng();
                    isDragging = false;
                    document.getElementById('preview').className = '';
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
                    // Also update Streamlit with the saved address
                    updateStreamlit(savedAddress, false);
                }} else {{
                    // Get initial address for the default location
                    updateLocationPreview(defaultLocation);
                }}
                
                // Force map to resize after a delay
                setTimeout(function() {{
                    map.invalidateSize();
                }}, 300);
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
                            timeout: 10000,
                            maximumAge: 0
                        }}
                    );
                }} else {{
                    alert('Error: Geolocation is not supported by your browser.');
                }}
            }}
            
            function updateLocationPreviewDuringDrag(latlng) {{
                // Lightweight version of updateLocationPreview for use during dragging
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name && isDragging) {{
                            document.getElementById('preview').innerHTML = `📍 ${{data.display_name}}`;
                        }}
                    }})
                    .catch(error => {{
                        console.error("Error in reverse geocoding:", error);
                    }});
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
                            updateStreamlit(address, false);
                        }}
                    }})
                    .catch(error => {{
                        console.error("Error in reverse geocoding:", error);
                        document.getElementById('preview').innerHTML = "Error loading address.";
                    }});
            }}
            
            function updateStreamlit(address, isConfirmed) {{
                // Send to Streamlit using the component communication API
                window.parent.postMessage({{
                    type: "streamlit:setComponentValue",
                    value: {{
                        address: address,
                        isConfirmed: isConfirmed,
                        key: componentKey
                    }}
                }}, "*");
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
                                updateStreamlit(address, true);
                                
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
            
            // Initialize map immediately as a fallback
            if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                setTimeout(initializeMap, 1);
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
    
    # Generate a unique key for this instance
    component_key = "location_picker"
    
    # Display the map component with increased height
    component_value = html(get_map_html(current_language, component_key), height=550, key=component_key)
    
    # Process any returned data from the component
    if component_value and isinstance(component_value, dict):
        if component_value.get('address'):
            # Store the selected address in session state
            st.session_state.selected_address = component_value['address']
            
            # If confirmed, update the confirmed address
            if component_value.get('isConfirmed'):
                st.session_state.confirmed_address = component_value['address']
    
    # Add a separate button to manually confirm the location
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Pre-fill with selected or confirmed address if available
        default_value = st.session_state.get('selected_address', st.session_state.confirmed_address)
        address = st.text_input(
            "Confirm your address", 
            value=default_value,
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
    if st.session_state.confirmed_address and st.session_state.confirmed_address != default_value:
        st.info(f"📍 Confirmed location: {st.session_state.confirmed_address}")
    
    # Return the confirmed address from session state
    return st.session_state.get("confirmed_address", "")
