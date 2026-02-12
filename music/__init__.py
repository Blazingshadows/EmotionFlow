"""
Music module for emotion-driven music recommendation.

This module handles music state management, Spotify integration,
dynamic song queuing, and adaptive playlist generation based on detected emotions.

Key Components:
- MusicState: Enum of possible music states (CALM, UPBEAT, INTENSE, etc.)
- SpotifyClient: Handles OAuth, playback, and dynamic song selection
- MusicStateController: Maps emotions to music states
- RollingPlayer: Orchestrates smooth transitions and queue management
- SongQueue: Manages the dynamic queue of upcoming songs
- AudioFeatures: Audio feature matching for intelligent song selection
"""

from .music_state import MusicState
from .spotify_client import SpotifyClient
from .state_controller import MusicStateController
from .rolling_player import RollingPlayer
from .song_queue import SongQueue, Song
from .audio_features import calculate_feature_score

__all__ = [
    'MusicState',
    'SpotifyClient',
    'MusicStateController',
    'RollingPlayer',
    'SongQueue',
    'Song',
    'calculate_feature_score'
