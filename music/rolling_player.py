import threading
import time
from music.music_state import MusicState


class RollingPlayer:
    """
    Manages smooth music playback transitions based on emotion states.
    
    Instead of switching entire playlists when emotion changes,
    this system queues 2-5 relevant songs for each emotion state
    and smoothly transitions to new songs when emotions change.
    """
    
    def __init__(self, spotify_client):
        self.spotify = spotify_client
        self.auto_mode = True
        self.current_state = None
        self.last_state_change_time = 0
        self.min_queue_threshold = 2  # Queue more songs when < 2 remain
        
    def on_state_change(self, state: MusicState) -> None:
        """
        Handle emotion state change by queueing appropriate songs.
        
        Args:
            state: New MusicState to transition to
        """
        if not self.auto_mode:
            return
        
        # Avoid rapid re-queuing
        now = time.time()
        if now - self.last_state_change_time < 2:
            return
        
        self.last_state_change_time = now
        self.current_state = state
        
        # Run in background thread to avoid blocking UI
        thread = threading.Thread(
            target=self._queue_for_state,
            args=(state,),
            daemon=True
        )
        thread.start()
    
    def _queue_for_state(self, state: MusicState) -> None:
        """
        Queue 2-5 songs for the given emotion state.
        
        Args:
            state: MusicState to queue songs for
        """
        try:
            print(f"\n[RollingPlayer] Queueing songs for {state.value}...")
            
            # Queue 3-5 songs (random count for variety)
            song_count = 3  # Could be random between 3-5
            self.spotify.queue_songs_for_state(state, count=song_count)
            
            print(f"[RollingPlayer] Queue updated for {state.value}")
            
        except Exception as e:
            print(f"[RollingPlayer] Error queuing songs: {e}")
    
    def check_and_refill_queue(self) -> None:
        """
        Check if queue is running low and refill if needed.
        Call periodically from the main UI loop.
        """
        queue_size = self.spotify.song_queue.queue_size()
        
        if queue_size < self.min_queue_threshold and self.current_state:
            print(f"[RollingPlayer] Queue low ({queue_size} songs), refilling...")
            self._queue_for_state(self.current_state)
    
    def set_auto_mode(self, enabled: bool) -> None:
        """
        Enable/disable automatic emotion-based music selection.
        
        Args:
            enabled: True to enable auto-adaptation
        """
        self.auto_mode = enabled
        print(f"[RollingPlayer] Auto-mode: {'ON' if enabled else 'OFF'}")
    
    def get_queue_status(self) -> dict:
        """
        Get current queue status for UI display.
        
        Returns:
            Dict with queue info
        """
        return {
            "current_state": self.current_state.value if self.current_state else None,
            "queue_size": self.spotify.song_queue.queue_size(),
            "songs_played": len(self.spotify.song_queue.get_played_songs()),
            "queue_duration_seconds": self.spotify.song_queue.estimate_queue_duration()
        }
    
    def finalize_session(self) -> str:
        """
        Create a playlist with all songs from this session.
        Call this when session ends.
        
        Returns:
            Playlist ID if created, empty string otherwise
        """
        print("\n[RollingPlayer] Creating session playlist...")
        return self.spotify.create_session_playlist()
