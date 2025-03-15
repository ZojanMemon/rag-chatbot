"""Location picker component with OpenStreetMap integration."""
import streamlit as st
import json
from streamlit.components.v1 import html

def get_map_html(current_language: str = "English") -> str:
    """Generate HTML for OpenStreetMap component with search."""
    # Translations
    if current_language == "Urdu":
        search_placeholder = "مقام تلاش کریں..."
        auto_detect_text = "موجودہ مقام کا پتہ لگائیں"
        confirm_text = "اس مقام کی تصدیق کریں"
        loading_text = "لوڈ ہو رہا ہے..."
        error_text = "خرابی"
    elif current_language == "Sindhi":
        search_placeholder = "مڪان ڳوليو..."
        auto_detect_text = "موجود مڪان جو پتو لڳايو"
        confirm_text = "هن مڪان جي تصديق ڪريو"
        loading_text = "لوڊ ٿي رهيو آهي..."
        error_text = "خرابي"
    else:  # English
        search_placeholder = "Search for a location..."
        auto_detect_text = "Detect Current Location"
        confirm_text = "Confirm Location"
        loading_text = "Loading..."
        error_text = "Error"

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
        <div id="preview">{loading_text}</div>
        <div class="controls">
            <button class="secondary" id="detect-btn" onclick="detectLocation()">{auto_detect_text}</button>
            <button class="primary" id="confirm-btn" onclick="confirmLocation()">{confirm_text}</button>
        </div>

        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <script>
            // Variables
            var map, marker, selectedLocation, currentAddress;
            var defaultLocation = [30.3753, 69.3451]; // Pakistan center
            
            // Function to send data to Streamlit
            function sendToStreamlit(data) {{
                // Create a custom event
                const event = new CustomEvent("streamlit:locationUpdate", {{
                    detail: {{ data: data }}
                }});
                
                // Dispatch the event
                window.dispatchEvent(event);
            }}
            
            // Initialize map
            function initializeMap() {{
                try {{
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
                    
                    // Get initial address for the default location
                    updateLocationPreview(defaultLocation);
                    
                    // Force map to resize after a delay
                    setTimeout(function() {{
                        map.invalidateSize();
                    }}, 300);
                }} catch (error) {{
                    console.error("Error initializing map:", error);
                    document.getElementById('preview').innerHTML = "{error_text}: " + error.message;
                }}
            }}
            
            function updateMarker(latlng) {{
                marker.setLatLng(latlng);
                updateLocationPreview(latlng);
            }}
            
            function detectLocation() {{
                if (navigator.geolocation) {{
                    document.getElementById('detect-btn').disabled = true;
                    document.getElementById('detect-btn').innerHTML = "{loading_text}";
                    
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
                            document.getElementById('preview').innerHTML = "{error_text}: " + error.message;
                            
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
                    document.getElementById('preview').innerHTML = "{error_text}: Geolocation is not supported by your browser.";
                }}
            }}
            
            function updateLocationPreview(latlng) {{
                selectedLocation = latlng;
                document.getElementById('preview').innerHTML = "{loading_text}";
                
                // Use Nominatim for reverse geocoding
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name) {{
                            currentAddress = data.display_name;
                            document.getElementById('preview').innerHTML = `📍 ${{currentAddress}}`;
                        }}
                    }})
                    .catch(error => {{
                        console.error("Error in reverse geocoding:", error);
                        document.getElementById('preview').innerHTML = "{error_text}: " + error.message;
                    }});
            }}
            
            function confirmLocation() {{
                if (selectedLocation) {{
                    document.getElementById('confirm-btn').disabled = true;
                    document.getElementById('confirm-btn').innerHTML = "{loading_text}";
                    
                    fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{selectedLocation[0]}}&lon=${{selectedLocation[1]}}&format=json`)
                        .then(response => response.json())
                        .then(data => {{
                            if (data.display_name) {{
                                var address = data.display_name;
                                
                                // Update UI
                                document.getElementById('preview').innerHTML = `✅ ${{address}}`;
                                
                                // Send to Streamlit
                                sendToStreamlit(address);
                                
                                document.getElementById('confirm-btn').disabled = false;
                                document.getElementById('confirm-btn').innerHTML = "{confirm_text}";
                            }}
                        }})
                        .catch(error => {{
                            console.error("Error confirming location:", error);
                            document.getElementById('preview').innerHTML = "{error_text}: " + error.message;
                            
                            document.getElementById('confirm-btn').disabled = false;
                            document.getElementById('confirm-btn').innerHTML = "{confirm_text}";
                        }});
                }} else {{
                    document.getElementById('preview').innerHTML = "{error_text}: Please select a location first.";
                }}
            }}
            
            // Initialize map when DOM is fully loaded
            document.addEventListener('DOMContentLoaded', initializeMap);
            
            // Initialize map immediately as a fallback
            if (document.readyState === 'complete' || document.readyState === 'interactive') {{
                setTimeout(initializeMap, 1);
            }}
        </script>
    </body>
    </html>
    """

def show_location_picker(current_language: str = "English") -> str:
    """Show location picker with OpenStreetMap integration."""
    # Initialize session state for confirmed address if not exists
    if "confirmed_address" not in st.session_state:
        st.session_state.confirmed_address = ""
    
    # Create a unique key for the component
    component_key = "location_picker"
    
    # Create a container for the map
    map_container = st.container()
    
    # Create a container for the confirmation status
    status_container = st.container()
    
    # Display the map in the container
    with map_container:
        # Display the map
        result = html(get_map_html(current_language), height=550, key=component_key)
        
        # If we got a result from the component, update the session state
        if result:
            st.session_state.confirmed_address = result
    
    # Display the confirmation status if we have an address
    with status_container:
        if st.session_state.confirmed_address:
            st.success(f"✅ Location confirmed: {st.session_state.confirmed_address}")
            
            # Add a button to clear the location
            if st.button("Clear Location"):
                st.session_state.confirmed_address = ""
                st.experimental_rerun()
    
    # Return the confirmed address
    return st.session_state.confirmed_address
