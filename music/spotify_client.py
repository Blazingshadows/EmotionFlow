import os
import random
import time
from collections import deque
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from music.music_state import MusicState
from music.audio_features import calculate_feature_score
from music.song_queue import Song, SongQueue
from dotenv import load_dotenv

load_dotenv()

class SpotifyClient:
    def __init__(self):
        print("[Spotify] Initializing SpotifyClient...")
        
        # Cache file in project root
        cache_path = os.path.join(os.getcwd(), ".spotipy_cache")
        print(f"[Spotify] Cache path: {cache_path}")
        
        try:
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
            print("[Spotify] ✓ Authentication successful")
        except Exception as e:
            print(f"[Spotify] ✗ Auth error: {e}")
            raise

        self.playlists = {
            MusicState.CALM: "spotify:playlist:0W018UoOiTF8ehaUiSzBlz",
            MusicState.UPBEAT: "spotify:playlist:37i9dQZF1EVJHK7Q1TBABQ",
            MusicState.INTENSE: "spotify:playlist:5dZIuUEvUXMrqRzfZrTJBF",
            MusicState.BACKGROUND: "spotify:playlist:5jYQ4O9Ii3tQcSbJMtVrk8",
            MusicState.ROCK: "spotify:playlist:37i9dQZF1DX2IvZJK5xwFt"
        }
        
        # Track failed playlist IDs to avoid repeated API calls
        self._failed_playlists = set()
        self._last_retry_time = {}
        self._recent_track_uris = deque(maxlen=500)
        self._recent_track_uris_by_state = {
            state: deque(maxlen=120) for state in self.playlists.keys()
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
        Falls back to keyword search if playlist fails.
        
        Args:
            state: MusicState to search for
            count: Number of songs to return
            
        Returns:
            List of Song objects
        """
        import time
        
        # First try playlist-based search
        songs = self._search_playlist(state, count)
        
        # If playlist fails, fall back to keyword search
        if not songs:
            print(f"[Spotify] Fallback: searching by keyword for {state.value}...")
            songs = self._search_by_keyword(state, count)
        
        return songs
    
    def _search_playlist(self, state: MusicState, count: int) -> list:
        """Search songs from a specific playlist"""
        try:
            playlist_uri = self.playlists.get(state)
            if not playlist_uri:
                return []
            
            # Check if this playlist has failed before (avoid repeated API errors)
            playlist_id = playlist_uri.split(":")[-1]
            if playlist_id in self._failed_playlists:
                # Wait before retrying failed playlists
                last_retry = self._last_retry_time.get(playlist_id, 0)
                time_since_retry = time.time() - last_retry
                if time_since_retry < 60:
                    return []

            playlist_meta = self.sp.playlist(playlist_id, fields="tracks.total")
            total_tracks = int(playlist_meta.get("tracks", {}).get("total", 0))
            if total_tracks <= 0:
                return []

            songs = []
            attempts = 0
            while len(songs) < count and attempts < 4:
                fetch_size = min(80, total_tracks)
                max_offset = max(0, total_tracks - fetch_size)
                offset = random.randint(0, max_offset) if max_offset > 0 else 0

                results = self.sp.playlist_tracks(playlist_id, limit=fetch_size, offset=offset)
                tracks = results.get("items", [])
                random.shuffle(tracks)

                for track_obj in tracks:
                    if len(songs) >= count:
                        break
                    if not track_obj.get("track"):
                        continue

                    track = track_obj["track"]
                    uri = track.get("uri")
                    if not uri:
                        continue
                    if uri in self._recent_track_uris:
                        continue
                    if uri in self._recent_track_uris_by_state.get(state, []):
                        continue

                    song = Song(
                        track_id=track.get("id"),
                        name=track.get("name"),
                        artist=", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                        duration_ms=track.get("duration_ms", 0),
                        uri=uri
                    )
                    songs.append(song)

                attempts += 1

            # If filtering was too strict, top up from latest sampled tracks.
            if len(songs) < count:
                fallback = self.sp.playlist_tracks(playlist_id, limit=min(50, total_tracks), offset=0)
                for track_obj in fallback.get("items", []):
                    if len(songs) >= count:
                        break
                    track = track_obj.get("track")
                    if not track:
                        continue
                    uri = track.get("uri")
                    if not uri or any(existing.uri == uri for existing in songs):
                        continue
                    songs.append(
                        Song(
                            track_id=track.get("id"),
                            name=track.get("name"),
                            artist=", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                            duration_ms=track.get("duration_ms", 0),
                            uri=uri,
                        )
                    )
            
            print(f"[Spotify] Found {len(songs)} songs from {state.value} playlist")
            return songs
            
        except Exception as e:
            playlist_id = self.playlists.get(state, "").split(":")[-1]
            error_str = str(e).lower()
            
            # Track permanent errors
            if "404" in error_str or "not found" in error_str:
                self._failed_playlists.add(playlist_id)
                self._last_retry_time[playlist_id] = time.time()
                print(f"[Spotify] Playlist not found: {state.value}")
            else:
                print(f"[Spotify] Playlist error: {e}")
            
            return []
    
    def _search_by_keyword(self, state: MusicState, count: int) -> list:
        """Fallback: search for songs by keyword/mood"""
        try:
            # Map emotions to search keywords
            keywords = {
                MusicState.CALM: "calm peaceful relaxing",
                MusicState.UPBEAT: "upbeat happy energetic pop",
                MusicState.INTENSE: "intense powerful rock metal",
                MusicState.BACKGROUND: "background ambient chill lofi",
                MusicState.ROCK: "rock alternative hard rock"
            }
            
            query = keywords.get(state, state.value.lower())
            print(f"[Spotify] Searching: '{query}'")
            
            offset = random.randint(0, 150)
            results = self.sp.search(q=query, type='track', limit=50, offset=offset)
            tracks = results.get('tracks', {}).get('items', [])
            
            if not tracks:
                return []
            
            # Convert to Song objects
            songs = []
            random.shuffle(tracks)
            for track in tracks:
                if len(songs) >= count:
                    break
                uri = track.get("uri")
                if not uri:
                    continue
                if uri in self._recent_track_uris:
                    continue
                if uri in self._recent_track_uris_by_state.get(state, []):
                    continue
                song = Song(
                    track_id=track.get("id"),
                    name=track.get("name"),
                    artist=", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                    duration_ms=track.get("duration_ms", 0),
                    uri=uri
                )
                songs.append(song)

            if len(songs) < count:
                for track in tracks:
                    if len(songs) >= count:
                        break
                    uri = track.get("uri")
                    if not uri or any(existing.uri == uri for existing in songs):
                        continue
                    songs.append(
                        Song(
                            track_id=track.get("id"),
                            name=track.get("name"),
                            artist=", ".join([a.get("name", "Unknown") for a in track.get("artists", [])]),
                            duration_ms=track.get("duration_ms", 0),
                            uri=uri,
                        )
                    )
            
            print(f"[Spotify] Found {len(songs)} songs via search")
            return songs
            
        except Exception as e:
            print(f"[Spotify] Search error: {e}")
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
            self._remember_recent_songs(songs, state)
            self.song_queue.add_songs(songs, state)
            self._add_queued_songs_to_playback(songs)

    def _remember_recent_songs(self, songs: list, state: MusicState) -> None:
        state_recent = self._recent_track_uris_by_state.get(state)
        for song in songs:
            if song.uri:
                self._recent_track_uris.append(song.uri)
                if state_recent is not None:
                    state_recent.append(song.uri)
    
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
        Runs in background thread to avoid blocking UI.
        
        Args:
            state: MusicState to start playing
        """
        import threading
        
        # Run in background thread to avoid blocking
        thread = threading.Thread(target=self._play_state_worker, args=(state,), daemon=True)
        thread.start()
    
    def _play_state_worker(self, state: MusicState) -> None:
        """
        Worker thread for starting playback.
        
        Args:
            state: MusicState to start playing
        """
        try:
            print(f"\n[Spotify] ▶ Starting playback for {state.value}...")
            
            # Get device with timeout
            device_id = self._get_device_safe()
            if not device_id:
                print(f"[Spotify] ✗ NO DEVICE FOUND")
                print(f"[Spotify] → Make sure Spotify app is OPEN and playing")
                print(f"[Spotify] → Or select a device in Spotify settings")
                return
            
            print(f"[Spotify] ✓ Device found: {device_id}")
            
            # Get songs
            songs = self.search_songs_by_state(state, count=5)
            if not songs:
                print(f"[Spotify] ✗ NO SONGS FOUND for {state.value}")
                return
            
            print(f"[Spotify] ✓ Got {len(songs)} songs")
            
            # Start playback with first song
            first_song = songs[0]
            print(f"[Spotify] ▶ Playing: {first_song.name} by {first_song.artist}")
            print(f"[Spotify] ▶ URI: {first_song.uri}")
            
            try:
                self.sp.start_playback(device_id=device_id, uris=[first_song.uri])
                print(f"[Spotify] ✓ PLAYBACK STARTED!")
            except Exception as e:
                print(f"[Spotify] ✗ PLAYBACK FAILED: {e}")
                return
            
            # Queue remaining songs
            if len(songs) > 1:
                print(f"[Spotify] ▶ Queueing {len(songs)-1} more songs...")
                self._add_queued_songs_to_playback(songs[1:])
            
            # Add all songs to queue manager
            self._remember_recent_songs(songs, state)
            self.song_queue.add_songs(songs, state)
            print(f"[Spotify] ✓ Queue manager updated")
            
        except Exception as e:
            print(f"[Spotify] ✗ PLAYBACK ERROR: {type(e).__name__}: {e}")
    
    def _get_device_safe(self):
        """
        Get active device with error handling.
        Returns device_id or None
        """
        try:
            devices = self.sp.devices()
            device_list = devices.get("devices", [])
            
            if not device_list:
                print("[Spotify] ✗ NO DEVICES FOUND")
                print("[Spotify] → Open Spotify app first")
                print("[Spotify] → Or check Settings > Apps > Connect devices")
                return None
            
            print(f"[Spotify] Found {len(device_list)} device(s):")
            for i, d in enumerate(device_list):
                active = "✓ ACTIVE" if d.get("is_active") else ""
                print(f"  {i+1}. {d.get('name')} ({d.get('type')}) {active}")
            
            # Try to find active device
            active_device = next((d for d in device_list if d.get("is_active")), None)
            target_device = active_device or device_list[0]
            
            device_id = target_device.get("id")
            device_name = target_device.get("name", "Unknown")
            
            if device_id and not active_device:
                print(f"[Spotify] → Activating: {device_name}")
                try:
                    self.sp.transfer_playback(device_id=device_id, force_play=True)
                except Exception as e:
                    print(f"[Spotify] Warning: Could not activate device: {e}")
            
            self.current_device_id = device_id
            return device_id
        except Exception as e:
            print(f"[Spotify] Error getting device: {e}")
            return None

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
