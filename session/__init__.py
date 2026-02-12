"""
Session module for tracking and analyzing user sessions.

This module provides functionality for managing user sessions,
tracking emotion history, and generating analytics.
"""

from .session_manager import SessionManager
from .analytics import SessionAnalytics

__all__ = ['SessionManager', 'SessionAnalytics']
