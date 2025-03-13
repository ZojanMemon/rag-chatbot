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
        let currentAddress = "";

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
            
            // Check if we have a previously saved location in localStorage
            try {{
                const savedAddress = localStorage.getItem('confirmedAddress');
                if (savedAddress) {{
                    document.getElementById('preview').innerHTML = `✅ ${{savedAddress}}`;
                    
                    // Send message to parent to update the address field
                    window.parent.postMessage({{
                        type: 'updateAddressField',
                        address: savedAddress,
                        confirmed: true
                    }}, '*');
                }}
            }} catch(e) {{
                console.error("Error checking localStorage:", e);
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
                        currentAddress = address;
                        document.getElementById('preview').innerHTML = `📍 ${{address}}`;
                        document.getElementById('confirm-btn').classList.remove('hidden');
                        
                        // Update the parent's text field with the address
                        try {{
                            window.parent.postMessage({{
                                type: 'updateAddressField',
                                address: address,
                                confirmed: false
                            }}, '*');
                        }} catch(e) {{
                            console.error("Error updating address field:", e);
                        }}
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
                            
                            // Update the parent's text field with the confirmed address
                            try {{
                                window.parent.postMessage({{
                                    type: 'updateAddressField',
                                    address: address,
                                    confirmed: true
                                }}, '*');
                            }} catch(e) {{
                                console.error("Error updating address field:", e);
                            }}
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
    # Initialize session state for address if not present
    if "temp_address" not in st.session_state:
        st.session_state.temp_address = ""
    
    # Display the map component
    html(get_map_html(current_language), height=500)
    
    # Add JavaScript to listen for messages from the iframe
    st.markdown("""
    <script>
    // Listen for messages from the iframe
    window.addEventListener('message', function(event) {
        if (event.data.type === 'updateAddressField') {
            // Find the address input field and update its value
            const addressInput = document.querySelector('input[aria-label="Confirm your address"]');
            if (addressInput) {
                addressInput.value = event.data.address;
                // Trigger an input event to notify Streamlit
                const inputEvent = new Event('input', { bubbles: true });
                addressInput.dispatchEvent(inputEvent);
                
                // If this is a confirmed address, also update the session state
                if (event.data.confirmed) {
                    // We need to use Streamlit's setComponentValue to update session state
                    // This is done indirectly by triggering a form submission
                    const confirmButton = document.querySelector('button[data-testid="baseButton-primary"]');
                    if (confirmButton) {
                        confirmButton.click();
                    }
                }
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Add a separate button to manually confirm the location
    col1, col2 = st.columns([3, 1])
    
    with col1:
        address = st.text_input("Confirm your address", key="manual_address_input", value=st.session_state.temp_address)
    
    with col2:
        if st.button("Confirm Address", type="primary"):
            if address:
                st.session_state.confirmed_address = address
                st.success(f"Location confirmed: {address}")
            else:
                st.error("Please enter an address")
    
    # Return the confirmed address from session state
    return st.session_state.get("confirmed_address", "")
