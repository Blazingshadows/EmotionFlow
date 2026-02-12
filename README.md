# Emotion Driven Music Recommendation System

An intelligent music recommendation system that analyzes user emotions through facial expression recognition and recommends music accordingly.

## Features

- Real-time emotion detection using facial recognition
- Music recommendation based on detected emotions
- Spotify integration for seamless playback
- Session analytics and emotion tracking
- User-friendly interface

## Project Structure

- `emotion/` - Emotion detection and facial analysis modules
- `music/` - Music recommendation and playback logic
- `session/` - Session management and analytics
- `ui/` - User interface components

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure settings in `config.py`
3. Run the application: `python app.py`

## Requirements

- Python 3.8+
- PyTorch
- OpenCV
- Spotify API credentials (for music playback)

## Models

The system uses pre-trained models for emotion detection:
- MiniXception model
- MobileNetV2 with AffectNet dataset
