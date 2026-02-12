# Emotion Driven Music Recommendation System

A real-time, desktop emotion-driven music system that detects facial expressions (and optional gesture triggers) to select and play Spotify playlists.

## Key Features

- **Real-time emotion recognition** using a MiniXception facial expression model
- **Stable emotion gating** to reduce rapid switches and false positives
- **Gesture-triggered “Rock” mode** using OpenCV-based hand contour detection
- **Adaptive music state controller** (Calm, Background, Upbeat, Intense, Rock)
- **Spotify playback integration** with OAuth token caching and device activation
- **Session analytics** with emotion and state logging
- **Desktop GUI** built with PyQt6 and live camera preview

## Tech Stack

- **Language:** Python 3.8+
- **UI:** PyQt6
- **Computer Vision:** OpenCV
- **Deep Learning:** PyTorch (MiniXception)
- **Music Playback:** Spotipy (Spotify Web API)
- **Session Analytics:** JSONL logging
- **OAuth:** Spotify OAuth with cached tokens

## Project Structure

- emotion/ - Emotion detection and gesture utilities
- music/ - Music state control and Spotify playback
- session/ - Session logging and analytics
- ui/ - PyQt6 interface and camera loop

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Add Spotify credentials in `.env`
3. Configure thresholds in `config.py`
4. Run the app: `python app.py`

## Spotify Requirements

- Spotify Developer App with Redirect URI configured
- Active Spotify device open (desktop or web player)
- Valid OAuth token cached in `.spotipy_cache`

## Models

- MiniXception facial expression model (7-class)
- Optional MobileNetV2 (AffectNet) checkpoints
