import requests
import os

def download_noto_sans():
    """Download Noto Sans Regular font that supports Sindhi."""
    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf"
    font_path = "NotoSans-Regular.ttf"
    
    if not os.path.exists(font_path):
        print("Downloading Noto Sans font...")
        response = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(response.content)
        print("Font downloaded successfully!")
    else:
        print("Font already exists!")

if __name__ == "__main__":
    download_noto_sans()
