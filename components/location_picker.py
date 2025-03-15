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
        select_location_text = "براہ کرم مقام منتخب کریں"
    elif current_language == "Sindhi":
        search_placeholder = "مڪان ڳوليو..."
        auto_detect_text = "موجود مڪان جو پتو لڳايو"
        confirm_text = "هن مڪان جي تصديق ڪريو"
        select_location_text = "مهرباني ڪري مڪان چونڊيو"
    else:  # English
        search_placeholder = "Search for a location..."
        auto_detect_text = "Detect Current Location"
        confirm_text = "Confirm This Location"
        select_location_text = "Please select a location"

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
            var selectedAddress = "";
            
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
                
                // Handle marker drag
                marker.on('dragend', function(e) {{
                    var pos = e.target.getLatLng();
                    updateLocationPreview([pos.lat, pos.lng]);
                }});
                
                // Handle map click
                map.on('click', function(e) {{
                    updateMarker([e.latlng.lat, e.latlng.lng]);
                }});
                
                // Force map to resize after a delay
                setTimeout(function() {{
                    map.invalidateSize();
                    // Get initial address for the default location
                    updateLocationPreview(defaultLocation);
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
            
            function updateLocationPreview(latlng) {{
                selectedLocation = latlng;
                document.getElementById('preview').innerHTML = "Loading address...";
                
                // Use Nominatim for reverse geocoding
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name) {{
                            var address = data.display_name;
                            selectedAddress = address;
                            document.getElementById('preview').innerHTML = `📍 ${{address}}`;
                        }}
                    }})
                    .catch(error => {{
                        console.error("Error in reverse geocoding:", error);
                        document.getElementById('preview').innerHTML = "Error loading address.";
                    }});
            }}
            
            function confirmLocation() {{
                if (selectedLocation && selectedAddress) {{
                    document.getElementById('confirm-btn').disabled = true;
                    document.getElementById('confirm-btn').innerHTML = "Confirming...";
                    
                    // Update UI
                    document.getElementById('preview').innerHTML = `✅ ${{selectedAddress}}`;
                    
                    // Send the confirmed address back to Python
                    window.parent.postMessage({{
                        type: 'streamlit:component-value',
                        value: selectedAddress
                    }}, '*');
                    
                    document.getElementById('confirm-btn').disabled = false;
                    document.getElementById('confirm-btn').innerHTML = "{confirm_text}";
                }} else {{
                    alert('{select_location_text}');
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

def show_location_picker(current_language: str = "English") -> str:
    """Show location picker with OpenStreetMap integration.
    
    Returns:
        str: The confirmed address
    """
    # Initialize session state for confirmed address if not exists
    if "confirmed_address" not in st.session_state:
        st.session_state.confirmed_address = ""
    
    # Display the map component
    selected_location = html(get_map_html(current_language), height=550)
    
    # Update session state if a location was selected
    if selected_location:
        st.session_state.confirmed_address = selected_location
        
        # Show success message
        if current_language == "Urdu":
            success_message = "✅ مقام کی تصدیق کر دی گئی"
        elif current_language == "Sindhi":
            success_message = "✅ مڪان جي تصديق ٿي وئي"
        else:  # English
            success_message = "✅ Location confirmed"
            
        st.success(success_message)
    
    # Return the confirmed address from session state
    return st.session_state.get("confirmed_address", "")
