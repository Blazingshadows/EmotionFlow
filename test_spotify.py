import os
from dotenv import load_dotenv
load_dotenv()

print("[1] Testing Spotify connection...")

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    
    cache_path = os.path.join(os.getcwd(), ".spotipy_cache")
    
    print("[2] Creating auth manager...")
    auth = SpotifyOAuth(
        client_id=os.getenv('SPOTIPY_CLIENT_ID'),
        client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
        redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback'),
        scope="user-modify-playback-state user-read-playback-state",
        cache_path=cache_path,
        show_dialog=False  # Don't show auth dialog
    )
    
    print("[3] Creating Spotify client...")
    sp = spotipy.Spotify(auth_manager=auth)
    
    print("[4] Getting devices...")
    devices = sp.devices()
    
    print(f"\n✓ Connected to Spotify!")
    print(f"Devices found: {len(devices['devices'])}")
    for d in devices['devices']:
        print(f"  - {d['name']} (Active: {d['is_active']})")
    
    if not devices['devices']:
        print("\n⚠️ No Spotify devices found!")
        print("Open Spotify app on your machine and try again.")
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")