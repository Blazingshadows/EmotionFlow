"""
Session Manager

Manages user sessions including emotion tracking, music history, and session persistence.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user sessions and emotion/music history.
    """
    
    def __init__(self, session_dir: str = "session"):
        """
        Initialize session manager.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        
        self.current_session: Optional[Dict] = None
        self.session_id: Optional[str] = None
    
    def start_session(self, user_id: Optional[str] = None) -> str:
        """
        Start a new session.
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            Session ID
        """
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.current_session = {
            'session_id': self.session_id,
            'user_id': user_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'emotion_history': [],
            'music_history': [],
            'events': []
        }
        
        logger.info(f"Started session: {self.session_id}")
        return self.session_id
    
    def end_session(self) -> None:
        """End the current session and save to disk."""
        if not self.current_session:
            logger.warning("No active session to end")
            return
        
        self.current_session['end_time'] = datetime.now().isoformat()
        self._save_session()
        
        logger.info(f"Ended session: {self.session_id}")
        self.current_session = None
        self.session_id = None
    
    def log_emotion(self, emotion: str, confidence: float, 
                   timestamp: Optional[str] = None) -> None:
        """
        Log an emotion detection event.
        
        Args:
            emotion: Detected emotion label
            confidence: Confidence score (0.0 to 1.0)
            timestamp: Optional timestamp (defaults to current time)
        """
        if not self.current_session:
            logger.warning("No active session for logging emotion")
            return
        
        emotion_event = {
            'emotion': emotion,
            'confidence': confidence,
            'timestamp': timestamp or datetime.now().isoformat()
        }
        
        self.current_session['emotion_history'].append(emotion_event)
    
    def log_music(self, track_name: str, artist: str, 
                 emotion: str, timestamp: Optional[str] = None) -> None:
        """
        Log a music playback event.
        
        Args:
            track_name: Name of the track
            artist: Artist name
            emotion: Emotion that triggered this track
            timestamp: Optional timestamp (defaults to current time)
        """
        if not self.current_session:
            logger.warning("No active session for logging music")
            return
        
        music_event = {
            'track_name': track_name,
            'artist': artist,
            'emotion': emotion,
            'timestamp': timestamp or datetime.now().isoformat()
        }
        
        self.current_session['music_history'].append(music_event)
    
    def log_event(self, event_type: str, data: Dict) -> None:
        """
        Log a custom event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if not self.current_session:
            logger.warning("No active session for logging event")
            return
        
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_session['events'].append(event)
    
    def get_current_session(self) -> Optional[Dict]:
        """Get the current session data."""
        return self.current_session
    
    def _save_session(self) -> None:
        """Save the current session to disk."""
        if not self.current_session:
            return
        
        filename = f"session_{self.session_id}.json"
        filepath = self.session_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.current_session, f, indent=2)
            logger.info(f"Saved session to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def load_session(self, session_id: str) -> Optional[Dict]:
        """
        Load a session from disk.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session data or None if not found
        """
        filename = f"session_{session_id}.json"
        filepath = self.session_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Session file not found: {filepath}")
            return None
        
        try:
            with open(filepath, 'r') as f:
                session_data = json.load(f)
            logger.info(f"Loaded session: {session_id}")
            return session_data
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """
        List all saved session IDs.
        
        Returns:
            List of session IDs
        """
        sessions = []
        for filepath in self.session_dir.glob("session_*.json"):
            session_id = filepath.stem.replace("session_", "")
            sessions.append(session_id)
        
        return sorted(sessions, reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session file.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        filename = f"session_{session_id}.json"
        filepath = self.session_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Session file not found: {filepath}")
            return False
        
        try:
            filepath.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def get_session_duration(self) -> Optional[float]:
        """
        Get the duration of the current session in seconds.
        
        Returns:
            Duration in seconds or None if no active session
        """
        if not self.current_session:
            return None
        
        start_time = datetime.fromisoformat(self.current_session['start_time'])
        current_time = datetime.now()
        
        duration = (current_time - start_time).total_seconds()
        return duration
