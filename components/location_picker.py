"""Location picker component with OpenStreetMap integration."""
import streamlit as st
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
        confirm_text = "Confirm This Location"
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
        <script>
            var map, marker, selectedLocation, currentAddress;
            var defaultLocation = [30.3753, 69.3451]; // Pakistan center
            
            // Initialize map
            function initMap() {{
                // Create map
                map = L.map('map').setView(defaultLocation, 5);
                
                // Add tile layer
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                
                // Create marker
                marker = L.marker(defaultLocation, {{ draggable: true }}).addTo(map);
                selectedLocation = defaultLocation;
                
                // Handle marker drag
                marker.on('dragend', function(e) {{
                    var pos = e.target.getLatLng();
                    selectedLocation = [pos.lat, pos.lng];
                    getAddressFromCoordinates(selectedLocation);
                }});
                
                // Handle map click
                map.on('click', function(e) {{
                    marker.setLatLng(e.latlng);
                    selectedLocation = [e.latlng.lat, e.latlng.lng];
                    getAddressFromCoordinates(selectedLocation);
                }});
                
                // Get initial address
                getAddressFromCoordinates(defaultLocation);
            }}
            
            // Get address from coordinates using Nominatim
            function getAddressFromCoordinates(latlng) {{
                document.getElementById('preview').innerHTML = "{loading_text}";
                
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name) {{
                            currentAddress = data.display_name;
                            document.getElementById('preview').innerHTML = `📍 ${{currentAddress}}`;
                        }} else {{
                            document.getElementById('preview').innerHTML = `📍 Latitude: ${{latlng[0].toFixed(6)}}, Longitude: ${{latlng[1].toFixed(6)}}`;
                        }}
                    }})
                    .catch(error => {{
                        document.getElementById('preview').innerHTML = `📍 Latitude: ${{latlng[0].toFixed(6)}}, Longitude: ${{latlng[1].toFixed(6)}}`;
                    }});
            }}
            
            // Detect current location
            function detectLocation() {{
                if (navigator.geolocation) {{
                    document.getElementById('detect-btn').disabled = true;
                    document.getElementById('detect-btn').innerHTML = "{loading_text}";
                    
                    navigator.geolocation.getCurrentPosition(
                        function(position) {{
                            var pos = [position.coords.latitude, position.coords.longitude];
                            map.setView(pos, 15);
                            marker.setLatLng(pos);
                            selectedLocation = pos;
                            getAddressFromCoordinates(selectedLocation);
                            
                            document.getElementById('detect-btn').disabled = false;
                            document.getElementById('detect-btn').innerHTML = "{auto_detect_text}";
                        }},
                        function(error) {{
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
                    document.getElementById('preview').innerHTML = "{error_text}: Geolocation not supported";
                }}
            }}
            
            // Confirm location
            function confirmLocation() {{
                if (selectedLocation) {{
                    // Get the current address from the preview
                    var addressToConfirm = document.getElementById('preview').innerText;
                    if (addressToConfirm.startsWith('📍 ')) {{
                        addressToConfirm = addressToConfirm.substring(2); // Remove the 📍 emoji
                    }}
                    
                    document.getElementById('preview').innerHTML = `✅ ${{addressToConfirm}}`;
                    
                    // Try to get the parent window to set a value
                    try {{
                        window.parent.postMessage({{
                            type: 'location',
                            value: addressToConfirm
                        }}, '*');
                    }} catch (e) {{
                        console.error("Error posting message:", e);
                    }}
                }}
            }}
            
            // Initialize map when page loads
            window.onload = initMap;
        </script>
    </body>
    </html>
    """

def show_location_picker(current_language: str = "English") -> str:
    """Show location picker with OpenStreetMap integration."""
    # Initialize session state for confirmed address if not exists
    if "confirmed_address" not in st.session_state:
        st.session_state.confirmed_address = ""
    
    # Display the map
    st.markdown("### Select your location on the map")
    html(get_map_html(current_language), height=550)
    
    # Manual input form
    with st.form("location_form"):
        location = st.text_input(
            "Or enter location manually",
            value=st.session_state.get("confirmed_address", "")
        )
        
        submit = st.form_submit_button("Confirm Location")
        
        if submit and location:
            st.session_state.confirmed_address = location
            st.success(f"✅ Location confirmed: {location}")
    
    # Add a button to clear the location if one is set
    if st.session_state.confirmed_address:
        if st.button("Clear Location"):
            st.session_state.confirmed_address = ""
            st.experimental_rerun()
    
    # Return the confirmed address
    return st.session_state.get("confirmed_address", "")
