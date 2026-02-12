"""
Song Queue Manager

Manages a queue of songs for dynamic playback.
Smoothly transitions between emotions by queuing relevant songs.
"""

import time
import threading
from collections import deque
from typing import List, Optional, Dict
from music.music_state import MusicState


class Song:
    """Represents a Spotify track"""
    def __init__(self, track_id: str, name: str, artist: str, duration_ms: int, uri: str):
        self.track_id = track_id
        self.name = name
        self.artist = artist
        self.duration_ms = duration_ms
        self.uri = uri
        self.state = None  # Which emotion state this song was queued for
        self.queued_at = time.time()
    
    def __repr__(self):
        return f"Song({self.name} - {self.artist})"


class SongQueue:
    """
    Manages a dynamic queue of songs.
    
    Workflow:
    - When emotion state is stable, queue 2-5 songs matching that state
    - When emotion changes, add 2-5 songs for new state to queue
    - At end of session, all played songs can be used to create mix playlist
    """
    
    def __init__(self, queue_size: int = 10):
        self.queue = deque(maxlen=queue_size)  # Current queue of upcoming songs
        self.played_songs: List[Song] = []     # Historical record of all songs
        self.current_song: Optional[Song] = None
        self.current_state: Optional[MusicState] = None
        self.lock = threading.Lock()
    
    def add_songs(self, songs: List[Song], state: MusicState) -> None:
        """
        Add songs to queue for a specific emotion state.
        
        Args:
            songs: List of Song objects to add
            state: MusicState these songs are for
        """
        with self.lock:
            for song in songs:
                song.state = state
                self.queue.append(song)
            print(f"[Queue] Added {len(songs)} songs for {state.value}")
    
    def get_next_songs(self, count: int = 5) -> List[str]:
        """
        Get next N songs as Spotify URIs.
        
        Args:
            count: Number of songs to return
            
        Returns:
            List of Spotify track URIs
        """
        with self.lock:
            uris = []
            # Peek at queue without removing
            for i in range(min(count, len(self.queue))):
                uris.append(self.queue[i].uri)
            return uris
    
    def pop_song(self) -> Optional[Song]:
        """
        Remove and return the next song from queue.
        Marks it as played.
        
        Returns:
            Next Song or None if queue empty
        """
        with self.lock:
            if not self.queue:
                return None
            
            song = self.queue.popleft()
            self.current_song = song
            self.played_songs.append(song)
            print(f"[Queue] Now playing: {song} ({song.state.value})")
            return song
    
    def peek_song(self) -> Optional[Song]:
        """Get next song without removing from queue"""
        with self.lock:
            if not self.queue:
                return None
            return self.queue[0]
    
    def queue_size(self) -> int:
        """Get current queue size"""
        with self.lock:
            return len(self.queue)
    
    def get_played_songs(self) -> List[Song]:
        """Get all songs that have been played"""
        with self.lock:
            return self.played_songs.copy()
    
    def get_state_distribution(self) -> Dict[MusicState, int]:
        """
        Get distribution of songs by emotion state.
        Useful for session summary.
        
        Returns:
            Dict mapping MusicState to count of songs
        """
        with self.lock:
            distribution = {}
            for song in self.played_songs:
                if song.state:
                    distribution[song.state] = distribution.get(song.state, 0) + 1
            return distribution
    
    def estimate_queue_duration(self) -> float:
        """
        Estimate total duration of queued songs in seconds.
        
        Returns:
            Total duration in seconds
        """
        with self.lock:
            total_ms = sum(song.duration_ms for song in self.queue)
            return total_ms / 1000.0
    
    def should_add_songs(self, threshold: int = 3) -> bool:
        """
        Check if queue is running low and needs more songs.
        
        Args:
            threshold: Add songs when queue size drops below this
            
        Returns:
            True if more songs should be added
        """
        with self.lock:
            return len(self.queue) < threshold
    
    def clear_queue(self) -> None:
        """Clear the queue (but keep history)"""
        with self.lock:
            self.queue.clear()
    
    def get_session_summary(self) -> Dict:
        """
        Get summary of songs played this session.
        
        Returns:
            Dict with song count, duration, state distribution, etc.
        """
        with self.lock:
            total_duration = sum(song.duration_ms for song in self.played_songs) / 1000.0
            state_dist = self.get_state_distribution()
            
            return {
                "total_songs_played": len(self.played_songs),
                "total_duration_seconds": total_duration,
                "songs_per_state": state_dist,
                "played_songs": [
                    {
                        "name": s.name,
                        "artist": s.artist,
                        "state": s.state.value if s.state else None,
                        "duration_seconds": s.duration_ms / 1000.0
                    }
                    for s in self.played_songs
                ]
            }
