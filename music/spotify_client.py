import os
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from music.music_state import MusicState
from music.audio_features import calculate_feature_score
from music.song_queue import Song, SongQueue
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
                scope="user-modify-playback-state user-read-playback-state playlist-modify-public playlist-modify-private",
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
        
        self.song_queue = SongQueue(queue_size=20)
        self.current_device_id = None
        self.current_user_id = None

    def get_playlist_name(self, state):
        return self.playlist_names.get(state, state.value)

    def _get_device(self):
        """Get active device or first available device"""
        try:
            devices = self.sp.devices()
            device_list = devices.get("devices", [])
            
            if not device_list:
                print("[Spotify] ✗ No devices found. Open Spotify and start playing something once.")
                return None
            
            # Try to find active device
            active_device = next((d for d in device_list if d.get("is_active")), None)
            target_device = active_device or device_list[0]
            
            device_id = target_device.get("id")
            if device_id and not active_device:
                print(f"[Spotify] Activating device: {target_device.get('name')}")
                self.sp.transfer_playback(device_id=device_id, force_play=True)
            
            self.current_device_id = device_id
            return device_id
        except Exception as e:
            print(f"[Spotify] Error getting device: {e}")
            return None
    
    def _get_user_id(self):
        """Get current user ID"""
        if self.current_user_id:
            return self.current_user_id
        try:
            user = self.sp.current_user()
            self.current_user_id = user.get("id")
            return self.current_user_id
        except:
            return None
    
    def search_songs_by_state(self, state: MusicState, count: int = 5) -> list:
        """
        Search for songs matching a music state using the seed playlists.
        Uses audio features to score and filter songs.
        
        Args:
            state: MusicState to search for
            count: Number of songs to return
            
        Returns:
            List of Song objects
        """
        try:
            playlist_uri = self.playlists.get(state)
            if not playlist_uri:
                return []
            
            # Get tracks from the seed playlist
            playlist_id = playlist_uri.split(":")[-1]
            results = self.sp.playlist_tracks(playlist_id, limit=50)
            tracks = results.get("items", [])
            
            # Get audio features for tracks
            track_ids = [t["track"]["id"] for t in tracks if t["track"]]
            if not track_ids:
                return []
            
            # Fetch audio features
            features_data = self.sp.audio_features(track_ids)
            
            # Score songs by how well they match the state
            scored_songs = []
            for i, track_obj in enumerate(tracks):
                if not track_obj.get("track"):
                    continue
                
                track = track_obj["track"]
                features = features_data[i] if i < len(features_data) else None
                
                if not features:
                    continue
                
                # Calculate match score
                score = calculate_feature_score(features, state)
                
                song = Song(
                    track_id=track.get("id"),
                    name=track.get("name"),
                    artist=", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                    duration_ms=track.get("duration_ms", 0),
                    uri=track.get("uri")
                )
                
                scored_songs.append((song, score))
            
            # Sort by score and return top N
            scored_songs.sort(key=lambda x: x[1], reverse=True)
            result = [song for song, score in scored_songs[:count]]
            
            print(f"[Spotify] Found {len(result)} songs for {state.value}")
            return result
            
        except Exception as e:
            print(f"[Spotify] Error searching songs: {e}")
            return []
    
    def queue_songs_for_state(self, state: MusicState, count: int = 5) -> None:
        """
        Search for and queue songs for a specific emotion state.
        
        Args:
            state: MusicState to queue for
            count: Number of songs to queue (2-5)
        """
        count = max(2, min(count, 5))  # Ensure 2-5 songs
        songs = self.search_songs_by_state(state, count=count)
        
        if songs:
            self.song_queue.add_songs(songs, state)
            self._add_queued_songs_to_playback(songs)
    
    def _add_queued_songs_to_playback(self, songs: list) -> None:
        """
        Add queued songs to Spotify playback queue.
        
        Args:
            songs: List of Song objects to add to queue
        """
        try:
            if not self.current_device_id:
                return
            
            for song in songs:
                self.sp.add_to_queue(song.uri, device_id=self.current_device_id)
                print(f"[Spotify] Queued: {song}")
        except Exception as e:
            print(f"[Spotify] Error adding to queue: {e}")
    
    def play_state(self, state: MusicState) -> None:
        """
        Start playback for a music state with dynamic song queueing.
        
        Args:
            state: MusicState to start playing
        """
        try:
            print(f"[Spotify] Starting playback for {state.value}...")
            
            # Get device
            device_id = self._get_device()
            if not device_id:
                return
            
            # Get first song
            songs = self.search_songs_by_state(state, count=5)
            if not songs:
                print(f"[Spotify] No songs found for {state.value}")
                return
            
            # Start playback with first song
            first_song = songs[0]
            self.sp.start_playback(device_id=device_id, uris=[first_song.uri])
            print(f"[Spotify] ✓ Now playing: {first_song}")
            
            # Queue remaining songs
            if len(songs) > 1:
                self._add_queued_songs_to_playback(songs[1:])
            
            # Add all songs to queue manager
            self.song_queue.add_songs(songs, state)
            
        except Exception as e:
            print(f"[Spotify] ✗ Error: {type(e).__name__}: {e}")

    def pause(self):
        try:
            self.sp.pause_playback(device_id=self.current_device_id)
        except:
            pass

    def next(self):
        try:
            self.sp.next_track(device_id=self.current_device_id)
        except:
            pass
    
    def create_session_playlist(self, session_name: str = "Emotion Mix") -> str:
        """
        Create a Spotify playlist with all songs played during the session.
        Useful for listening to the mixed emotions later.
        
        Args:
            session_name: Name for the created playlist
            
        Returns:
            Playlist ID or empty string if failed
        """
        try:
            user_id = self._get_user_id()
            if not user_id:
                print("[Spotify] Cannot create playlist: user not authenticated")
                return ""
            
            played_songs = self.song_queue.get_played_songs()
            if not played_songs:
                print("[Spotify] No songs to create playlist from")
                return ""
            
            # Create playlist
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            playlist_name = f"{session_name} - {timestamp}"
            
            playlist = self.sp.user_playlist_create(
                user_id,
                playlist_name,
                public=False,
                description="Auto-generated from Emotion Driven Music session"
            )
            
            playlist_id = playlist.get("id")
            print(f"[Spotify] Created playlist: {playlist_name}")
            
            # Add songs to playlist (Spotify API limits to 100 per request)
            song_uris = [song.uri for song in played_songs]
            for i in range(0, len(song_uris), 100):
                batch = song_uris[i:i+100]
                self.sp.playlist_add_items(playlist_id, batch)
            
            print(f"[Spotify] ✓ Added {len(song_uris)} songs to playlist")
            return playlist_id
            
        except Exception as e:
            print(f"[Spotify] Error creating playlist: {e}")
            return ""
