"""
Music module for emotion-driven music recommendation.

This module handles music state management, Spotify integration,
and adaptive playlist generation based on detected emotions.
"""

from .music_state import MusicState
from .spotify_client import SpotifyClient
from .state_controller import MusicStateController
from .rolling_player import RollingPlayer

__all__ = [
    'MusicState',
    'SpotifyClient',
    'MusicStateController',
    'RollingPlayer'
]
