import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from music.music_state import MusicState
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self):
        # Cache file in project root
        cache_path = os.path.join(os.getcwd(), ".spotipy_cache")
        
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:8888/callback'),
                scope="user-modify-playback-state user-read-playback-state",
                cache_path=cache_path,
                show_dialog=True
            )
        )

        self.playlists = {
            MusicState.CALM: "spotify:playlist:37i9dQZF1EIfTmpqlGn32s",
            MusicState.UPBEAT: "spotify:playlist:37i9dQZF1EVJHK7Q1TBABQ",
            MusicState.INTENSE: "spotify:playlist:37i9dQZF1EIdHZWT31d1QN",
            MusicState.BACKGROUND: "spotify:playlist:37i9dQZF1EIdNttkh5bOjS",
            MusicState.ROCK: "spotify:playlist:37i9dQZF1EIf9QdS3bOrgZ"
        }

        self.playlist_names = {
            MusicState.CALM: "Calm",
            MusicState.UPBEAT: "Upbeat",
            MusicState.INTENSE: "Intense",
            MusicState.BACKGROUND: "Background",
            MusicState.ROCK: "Rock"
        }

    def get_playlist_name(self, state):
        return self.playlist_names.get(state, state.value)

    def play_state(self, state):
        try:
            print(f"[Spotify] Attempting to play {state.value} playlist...")
            
            # Get devices and activate one if needed
            devices = self.sp.devices()
            device_list = devices.get("devices", [])
            print(f"[Spotify] Available devices: {[d['name'] for d in device_list]}")

            if not device_list:
                print("[Spotify] ✗ No devices found. Open Spotify and start playing something once.")
                return

            active_device = next((d for d in device_list if d.get("is_active")), None)
            target_device = active_device or device_list[0]
            device_id = target_device.get("id")
            device_name = target_device.get("name")

            if device_id:
                if not active_device:
                    print(f"[Spotify] Activating device: {device_name}")
                self.sp.transfer_playback(device_id=device_id, force_play=True)

            self.sp.start_playback(device_id=device_id, context_uri=self.playlists[state])
            print(f"[Spotify] ✓ Playing {state.value}")
        except Exception as e:
            print(f"[Spotify] ✗ Error: {type(e).__name__}: {e}")

    def pause(self):
        try:
            self.sp.pause_playback()
        except:
            pass

    def next(self):
        try:
            self.sp.next_track()
        except:
            pass
