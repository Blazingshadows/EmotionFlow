import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("[1] Importing Spotify...")
import spotipy
from spotipy.oauth2 import SpotifyOAuth

cache_path = os.path.join(os.getcwd(), ".spotipy_cache")

print("[2] Creating auth manager...")
auth = SpotifyOAuth(
    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
    redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI'),
    scope="user-modify-playback-state user-read-playback-state",
    cache_path=cache_path,
    open_browser=True
)

print("[3] Getting access token...")
token_info = auth.get_access_token(as_dict=True)
print(f"[✓] Got token: {token_info.get('access_token')[:20]}...")

print("[4] Creating Spotify client...")
sp = spotipy.Spotify(auth=token_info['access_token'])

print("[5] Fetching devices (this may take 5 seconds)...")
try:
    devices = sp.devices()
    print(f"\n[✓] Found {len(devices['devices'])} device(s):")
    for d in devices['devices']:
        status = "ACTIVE" if d['is_active'] else "inactive"
        print(f"    {d['name']} ({status})")
except Exception as e:
    print(f"[✗] Error getting devices: {e}")

print("\n[Done] You can close this now.")