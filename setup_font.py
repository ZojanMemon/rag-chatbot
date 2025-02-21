import requests
import os

def download_dejavu_font():
    """Download DejaVu Sans Condensed font that supports multiple languages."""
    font_url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSansCondensed.ttf"
    font_path = "DejaVuSansCondensed.ttf"
    
    if not os.path.exists(font_path):
        print("Downloading DejaVu Sans Condensed font...")
        response = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(response.content)
        print("Font downloaded successfully!")
    else:
        print("Font already exists!")

if __name__ == "__main__":
    download_dejavu_font()
