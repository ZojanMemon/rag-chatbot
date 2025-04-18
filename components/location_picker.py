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
        copy_text = "پتہ کاپی کریں"
        copied_text = "کاپی ہو گیا"
    elif current_language == "Sindhi":
        search_placeholder = "مڪان ڳوليو..."
        auto_detect_text = "موجود مڪان جو پتو لڳايو"
        copy_text = "پتو ڪاپي ڪريو"
        copied_text = "ڪاپي ٿي ويو"
    else:  # English
        search_placeholder = "Search for a location..."
        auto_detect_text = "Detect Current Location"
        copy_text = "Copy Address"
        copied_text = "Copied!"

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
                transition: all 0.2s ease;
            }}
            button:disabled {{
                opacity: 0.6;
                cursor: not-allowed;
            }}
            .primary {{
                background-color: #0066cc;
                color: white;
            }}
            .primary:hover:not(:disabled) {{
                background-color: #0052a3;
            }}
            .secondary {{
                background-color: #f0f2f6;
                color: #262730;
            }}
            .secondary:hover:not(:disabled) {{
                background-color: #e6e9ef;
            }}
            #preview {{
                margin-top: 10px;
                padding: 10px;
                background-color: #f0f2f6;
                border-radius: 4px;
                font-size: 14px;
                min-height: 20px;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }}
            #preview:hover {{
                background-color: #e6e9ef;
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
            .copy-success {{
                background-color: #e6ffe6 !important;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div id="preview" onclick="copyAddress()"></div>
        <div class="controls">
            <button class="secondary" id="detect-btn" onclick="detectLocation()">{auto_detect_text}</button>
            <button class="primary" id="copy-btn" onclick="copyAddress()" disabled>{copy_text}</button>
        </div>

        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://unpkg.com/leaflet-control-geocoder/dist/Control.Geocoder.js"></script>
        <script>
            var map, marker, selectedLocation, currentAddress;
            var defaultLocation = [30.3753, 69.3451]; // Pakistan center
            var copyButton = document.getElementById('copy-btn');
            var previewDiv = document.getElementById('preview');
            
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
                previewDiv.innerHTML = "Loading address...";
                copyButton.disabled = true;
                
                // Use Nominatim for reverse geocoding
                fetch(`https://nominatim.openstreetmap.org/reverse?lat=${{latlng[0]}}&lon=${{latlng[1]}}&format=json`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.display_name) {{
                            currentAddress = data.display_name;
                            previewDiv.innerHTML = "📍 " + currentAddress;
                            copyButton.disabled = false;
                            
                            // Send the selected address to Streamlit
                            window.parent.postMessage({{
                                type: 'selectedAddress',
                                address: currentAddress
                            }}, '*');
                        }}
                    }})
                    .catch(error => {{
                        console.error("Error in reverse geocoding:", error);
                        previewDiv.innerHTML = "Error loading address.";
                        copyButton.disabled = true;
                        currentAddress = null;
                    }});
            }}
            
            async function copyAddress() {{
                if (!currentAddress) return;
                
                try {{
                    await navigator.clipboard.writeText(currentAddress);
                    
                    // Visual feedback
                    previewDiv.classList.add('copy-success');
                    copyButton.innerHTML = "{copied_text}";
                    
                    // Reset after 1 second
                    setTimeout(() => {{
                        previewDiv.classList.remove('copy-success');
                        copyButton.innerHTML = "{copy_text}";
                    }}, 1000);
                    
                }} catch (err) {{
                    console.error('Failed to copy text: ', err);
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
    """Show location picker with OpenStreetMap integration."""
    # Initialize session state for confirmed address if not exists
    if "confirmed_address" not in st.session_state:
        st.session_state.confirmed_address = ""
    
    # Simple implementation without complex component callbacks
    map_html = get_map_html(current_language)
    html(map_html, height=550)
    
    # Add a simple form for manual address confirmation
    with st.form(key="location_form"):
        # Pre-fill with any address from the map if available
        address = st.text_input(
            "Confirm your location",
            value=st.session_state.get("confirmed_address", ""),
            key="manual_address_input"
        )
        
        # Submit button with language-specific labels
        if current_language == "Urdu":
            submit_label = "مقام کی تصدیق کریں"
            success_message = "✅ مقام کی تصدیق ہو گئی"
        elif current_language == "Sindhi":
            submit_label = "مڪان جي تصديق ڪريو"
            success_message = "✅ مڪان جي تصديق ٿي وئي"
        else:  # English
            submit_label = "Confirm Address"
            success_message = "✅ Location Confirmed"
            
        # Submit button
        submit = st.form_submit_button(submit_label)
        if submit and address:
            st.session_state.confirmed_address = address
            # Show clean success message
            st.success(success_message)
    
    # Return the confirmed address from session state
    return st.session_state.get("confirmed_address", "")
