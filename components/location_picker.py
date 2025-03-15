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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css"/>
        <link rel="stylesheet" href="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.css"/>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
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
                transition: all 0.2s;
            }}
            button:hover {{
                opacity: 0.9;
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
            /* Style for the search control */
            .leaflet-control-geocoder {{
                clear: both;
                margin: 10px !important;
                max-width: 300px !important;
            }}
            .leaflet-control-geocoder-form input {{
                padding: 8px 12px !important;
                border: 1px solid #ccc !important;
                border-radius: 4px !important;
                width: 100% !important;
                font-size: 14px !important;
            }}
            /* Style for the location marker */
            .leaflet-marker-icon {{
                filter: hue-rotate(340deg);
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

        // Function to send data back to Streamlit
        function sendToStreamlit(data) {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                value: data
            }}, '*');
        }}

        function initMap() {{
            const defaultLocation = [30.3753, 69.3451];

            // Initialize map
            map = L.map('map', {{
                zoomControl: true,
                scrollWheelZoom: true
            }}).setView(defaultLocation, 6);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap contributors'
            }}).addTo(map);

            // Add search control with custom styling
            const geocoder = L.Control.geocoder({{
                defaultMarkGeocode: false,
                placeholder: "{search_placeholder}",
                collapsed: false,
                position: 'topleft',
                geocoder: L.Control.Geocoder.nominatim({{
                    geocodingQueryParams: {{
                        countrycodes: 'pk',
                        viewbox: '60.8742,37.0974,77.8401,23.6345',
                        bounded: 1
                    }}
                }})
            }}).addTo(map);

            geocoder.on('markgeocode', function(e) {{
                const location = e.geocode.center;
                updateMarker([location.lat, location.lng]);
                map.setView(location, 17);
            }});

            // Add marker with custom icon
            const markerIcon = L.icon({{
                iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
                iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            }});

            marker = L.marker(defaultLocation, {{
                draggable: true,
                icon: markerIcon
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

            // Try to restore previous location
            const savedAddress = localStorage.getItem('confirmedAddress');
            if (savedAddress) {{
                document.getElementById('preview').innerHTML = `📍 ${{savedAddress}}`;
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
            
            // Show loading state
            document.getElementById('preview').innerHTML = '📍 Loading address...';
            document.getElementById('confirm-btn').classList.remove('hidden');
            document.getElementById('confirm-btn').style.backgroundColor = '#FF4B4B';
            
            // Use Nominatim for reverse geocoding with better error handling
            fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json&addressdetails=1`)
                .then(response => {{
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                }})
                .then(data => {{
                    if (data.display_name) {{
                        const address = data.display_name;
                        document.getElementById('preview').innerHTML = `📍 ${{address}}`;
                        sendToStreamlit(address);
                    }} else {{
                        throw new Error('No address found');
                    }}
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    document.getElementById('preview').innerHTML = '❌ Error loading address. Please try again.';
                }});
        }}

        function confirmLocation() {{
            if (selectedLocation) {{
                // Show loading state
                document.getElementById('preview').innerHTML = '⏳ Confirming location...';
                
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{selectedLocation[0]}}&lon=${{selectedLocation[1]}}&format=json&addressdetails=1`)
                    .then(response => {{
                        if (!response.ok) throw new Error('Network response was not ok');
                        return response.json();
                    }})
                    .then(data => {{
                        if (data.display_name) {{
                            const address = data.display_name;
                            confirmedLocation = address;
                            
                            // Store the address
                            localStorage.setItem('confirmedAddress', address);
                            
                            // Update UI with success state
                            document.getElementById('preview').innerHTML = `✅ ${{address}}`;
                            document.getElementById('confirm-btn').style.backgroundColor = '#28a745';
                            
                            // Send confirmed address to Streamlit
                            sendToStreamlit(`✅ ${{address}}`);
                        }} else {{
                            throw new Error('No address found');
                        }}
                    }})
                    .catch(error => {{
                        console.error('Error:', error);
                        document.getElementById('preview').innerHTML = '❌ Error confirming location. Please try again.';
                        document.getElementById('confirm-btn').style.backgroundColor = '#FF4B4B';
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
    # Initialize session state for location if not exists
    if 'confirmed_location' not in st.session_state:
        st.session_state.confirmed_location = None

    # Display the map component
    location_value = html(get_map_html(current_language), height=500)
    
    if location_value is not None:
        st.session_state.confirmed_location = location_value
        
    return st.session_state.confirmed_location
