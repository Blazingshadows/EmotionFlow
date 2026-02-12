import os
import webbrowser
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

cache_path = os.path.join(os.getcwd(), ".spotipy_cache")

auth = SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    scope="user-modify-playback-state user-read-playback-state",
    cache_path=cache_path,
    open_browser=False
)

# Get auth URL
auth_url = auth.get_authorize_url()
print(f"Open this URL in your browser:\n{auth_url}\n")
webbrowser.open(auth_url)

# Manually enter code
code = input("After authorizing, paste the full redirect URL here:\n> ")

# Extract code from redirect URL
if "code=" in code:
    code = code.split("code=")[1].split("&")[0]
    print(f"Extracted code: {code}")

# Save token
token = auth.get_access_token(code)
print(f"\n✓ Token saved! You can now run: python app.py")
