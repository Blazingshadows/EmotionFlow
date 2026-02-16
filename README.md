# Emotion-Driven Music Recommendation System

A real-time emotion detection and music recommendation system that analyzes facial expressions via webcam and dynamically curates Spotify playlists based on detected emotional states.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-red)](https://pytorch.org/)
[![Spotify](https://img.shields.io/badge/Spotify-API-green)](https://developer.spotify.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)

---

## 🎯 Overview

This system bridges computer vision and music recommendation by:
- **Detecting emotions** from live webcam feed using deep learning (CNN-based models)
- **Mapping emotions to music states** with stability controls and cooldown mechanisms
- **Dynamically queuing songs** based on audio feature matching (energy, valence, tempo, etc.)
- **Creating session playlists** on Spotify for post-session replay
- **Tracking analytics** for emotion distribution, state transitions, and playback history

### Key Metrics
- **Model Accuracy:** 74.71% on AffectNet validation set (4,532 samples)
- **Emotion Stability:** 15-frame sliding window + 3s minimum stable time
- **State Cooldown:** 5s between transitions to prevent rapid switching
- **Queue Size:** 2-5 songs per emotion state, auto-refills at <2 songs
- **Audio Feature Scoring:** 0.0-1.0 match score based on 5 Spotify features

---

## ✨ Features

### Core Capabilities
- ✅ **Real-Time Emotion Detection** – 7 emotion classes (Happy, Sad, Angry, Fear, Surprise, Disgust, Neutral)
- ✅ **Gesture Recognition** – Hand gesture detection for "Rock" mode override
- ✅ **Dynamic Song Queuing** – Audio feature-based matching (energy, valence, danceability, tempo, acousticness)
- ✅ **Smooth Playback Transitions** – Queue-based system prevents jarring playlist switches
- ✅ **Session Analytics** – Emotion distribution, state transitions, duration tracking
- ✅ **Spotify Integration** – OAuth2 authentication, playlist creation, playback control
- ✅ **Privacy Modes** – Private (no logging) and Public (full analytics) session options

### Technical Highlights
- **Signal Stability System:** 15-frame buffer with weighted voting to eliminate flicker
- **State Machine Logic:** Deterministic emotion→state mapping with configurable thresholds
- **Thread-Safe Queue:** Concurrent operations for UI updates and background song fetching
- **Error Resilience:** Graceful handling of camera/Spotify unavailability

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (PyQt6)               │
│  [ Webcam Feed ] [ Emotion Label ] [ Queue Status ]          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    EMOTION DETECTION PIPELINE                │
│  Webcam → Face Detection → Preprocessing → CNN Inference     │
│  → Confidence Filter → Stability Smoothing → Emotion Output  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    MUSIC STATE CONTROLLER                    │
│  Emotion → State Mapping → Cooldown Check → State Change     │
│  (Happy→UPBEAT, Sad→CALM, Angry→INTENSE, etc.)              │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    ROLLING PLAYER ENGINE                     │
│  State Change → Search Songs → Score by Features → Queue     │
│  Monitor Queue → Auto-Refill → Playback Control              │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    SPOTIFY CLIENT (Spotipy)                  │
│  OAuth2 Auth → Device Detection → Queue Songs → Create       │
│  Session Playlist → Play/Pause/Skip Control                  │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Frame → Emotion (7 classes) → Stability (15 frames) → State (5 types) → 
Queue (2-5 songs) → Playback → Analytics → Session Playlist
```

---

## 🚀 Installation

### Prerequisites
- **Python:** 3.8 or higher
- **Operating System:** Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Spotify Account:** Free or Premium (Premium required for device control)
- **Webcam:** Built-in or USB camera
- **Internet Connection:** Required for Spotify API

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd "Emotion Driven Music Recommendation System"
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Download Pre-trained Models
Models are already included in the repository:
- `assets/minixception_torch.pth` – MiniXception model (FER2013)
- `mobilenetv2_affectnet_yolo_final.pth` – MobileNetV2 (AffectNet)
- `checkpoints/minixception_best.pth` – Best checkpoint

### Step 5: Configure Spotify API

1. **Create Spotify App:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Note your `Client ID` and `Client Secret`
   - Add redirect URI: `http://127.0.0.1:8888/callback`

2. **Set Environment Variables:**
   Create a `.env` file in the project root:
   ```env
   SPOTIPY_CLIENT_ID=your_client_id_here
   SPOTIPY_CLIENT_SECRET=your_client_secret_here
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
   ```

### Step 6: First-Time Authentication
```bash
python first_auth.py
```
This will open a browser for Spotify OAuth. Authorize the app and copy the redirect URL back to the terminal.

---

## 🎮 Usage

### Basic Usage

1. **Launch Application:**
   ```bash
   python app.py
   ```

2. **Start Session:**
   - Click **"Start Session"** button
   - Camera will activate and emotion detection begins
   - Spotify playback starts automatically after 3s stable emotion

3. **During Session:**
   - UI displays: Current emotion, confidence, music state, queue size
   - Music adapts smoothly based on detected emotions
   - Queue auto-refills to maintain continuous playback

4. **End Session:**
   - Click **"Stop Session"** button
   - Session summary chart displays emotion distribution
   - Spotify playlist created: `"Emotion Mix - YYYY-MM-DD HH:MM"`

### Manual Controls

- **Auto-Adapt Mode:** Toggle automatic emotion-based transitions
- **Spotify Controls:** Use Spotify app for play/pause/skip
- **Queue Monitoring:** Real-time queue size visible in UI

---

## ⚙️ Configuration

### Key Parameters (`config.py`)

```python
# Emotion Stability
CONFIDENCE_THRESHOLD = 0.5        # Minimum confidence for emotion detection
MIN_EMOTION_STABLE_TIME = 3       # Seconds before emotion change triggers state change

# Music State Control
STATE_COOLDOWN = 5                # Seconds between state transitions

# Session
DEFAULT_SESSION_MODE = "PRIVATE"  # "PRIVATE" or "PUBLIC" (affects logging)
```

### Audio Feature Targets (`music/audio_features.py`)

Customize emotion→feature mappings:

```python
STATE_AUDIO_FEATURES = {
    MusicState.UPBEAT: {
        "energy": (0.6, 1.0),      # High energy
        "valence": (0.6, 1.0),     # Positive mood
        "danceability": (0.6, 1.0),
        "tempo": (120, 180)        # 120-180 BPM
    },
    MusicState.CALM: {
        "energy": (0.0, 0.4),      # Low energy
        "valence": (0.0, 0.5),     # Negative/neutral mood
        "tempo": (60, 100)         # Slow tempo
    }
    # ... more states
}
```

### Queue Settings (`music/rolling_player.py`)

```python
self.min_queue_threshold = 2      # Refill when queue < 2 songs
self.spotify_client.song_queue.max_size = 20  # Max queue capacity
```

---

## 📁 Project Structure

```
Emotion Driven Music Recommendation System/
├── app.py                          # Application entry point
├── config.py                       # Global configuration
├── requirements.txt                # Python dependencies
├── .env                            # Spotify API credentials (create this)
│
├── emotion/                        # Emotion detection module
│   ├── detector.py                 # CNN-based emotion detector
│   ├── detector_mobilenet.py      # MobileNetV2 variant
│   ├── face_utils.py               # Face detection utilities
│   ├── gesture_detector.py        # Hand gesture recognition
│   └── stability.py                # Signal smoothing & stability
│
├── music/                          # Music recommendation module
│   ├── audio_features.py           # Audio feature definitions & scoring
│   ├── music_state.py              # Music state enum (UPBEAT, CALM, etc.)
│   ├── rolling_player.py           # Playback orchestrator
│   ├── song_queue.py               # Thread-safe queue manager
│   ├── spotify_client.py           # Spotify API integration
│   └── state_controller.py        # Emotion→state logic
│
├── session/                        # Session management
│   ├── analytics.py                # Analytics calculation
│   ├── session_manager.py          # Session lifecycle
│   └── session_*.json              # Saved session data
│
├── ui/                             # User interface
│   └── window.py                   # PyQt6 main window
│
├── training/                       # Model training scripts
│   ├── train_minixception.py      # Train emotion classifier
│   ├── affectnet.py                # AffectNet dataset loader
│   └── evaluation.py               # Model evaluation
│
├── assets/                         # Pre-trained models
│   └── minixception_torch.pth      # MiniXception weights
│
├── md_export/                      # Documentation
│   ├── DOCUMENTATION_INDEX.md      # Doc navigation
│   ├── QUICK_REFERENCE.md          # Quick start guide
│   ├── DYNAMIC_QUEUE_SYSTEM.md     # Queue system explanation
│   └── ARCHITECTURE_DIAGRAMS.md    # Visual diagrams
│
└── FER2013/                        # Training dataset (if available)
    ├── train/
    └── test/
```

---

## 🧠 Model Performance

### Emotion Classification (AffectNet Dataset)

| Emotion  | Precision | Recall | F1-Score | Support |
|----------|-----------|--------|----------|---------|
| Angry    | 0.688     | 0.725  | 0.706    | 712     |
| Disgust  | 0.695     | 0.777  | 0.733    | 618     |
| Fear     | 0.701     | 0.676  | 0.688    | 672     |
| Happy    | 0.860     | 0.847  | 0.853    | 622     |
| Sad      | 0.879     | 0.875  | 0.877    | 791     |
| Surprise | 0.678     | 0.638  | 0.657    | 514     |
| Neutral  | 0.696     | 0.645  | 0.670    | 603     |
| **Accuracy** | -     | -      | **0.747** | **4,532** |

### Model Characteristics
- **Architecture:** MiniXception (lightweight CNN)
- **Parameters:** ~600K (CPU-friendly)
- **Inference Time:** ~15-20ms per frame on CPU
- **Input Size:** 48×48 grayscale images
- **Training Dataset:** FER2013 + AffectNet (partial)

---

## 🔧 API Reference

### Emotion Detection Module

```python
from emotion.detector import EmotionDetector

detector = EmotionDetector()
emotion, confidence = detector.predict_frame(frame)
# Returns: ("happy", 0.87)
```

### Music State Controller

```python
from music.state_controller import MusicStateController

controller = MusicStateController()
state_changed = controller.update(emotion, duration)
current_state = controller.get_current_state()
# Returns: MusicState.UPBEAT
```

### Spotify Client

```python
from music.spotify_client import SpotifyClient

client = SpotifyClient()
client.queue_songs_for_state(MusicState.UPBEAT, count=5)
playlist_id = client.create_session_playlist("My Session")
```

### Song Queue

```python
from music.song_queue import SongQueue

queue = SongQueue(max_size=20)
queue.add_songs(songs)
song = queue.pop_song()  # Mark as played
history = queue.get_played_songs()
```

---

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Test camera indices
python -c "import cv2; [print(f'Camera {i}: {cv2.VideoCapture(i).isOpened()}') for i in range(4)]"
```

### Spotify Device Not Found
- Ensure Spotify app is open and active on any device
- Try playing any song manually to activate device
- Check `sp.devices()` returns non-empty list

### OAuth Token Expired
```bash
# Delete cache and re-authenticate
rm .spotipy_cache
python first_auth.py
```

### Model Loading Error
- Verify model files exist in `assets/` and root directory
- Check PyTorch version compatibility: `pip install torch>=2.0`

### Queue Not Refilling
- Check internet connection (fetches audio features from Spotify)
- Verify Spotify playlists are accessible
- Enable debug logging: Add `print()` statements in `rolling_player.py`

---

## 📊 Session Analytics

Session data is saved in `session/` directory as JSON files:

```json
{
  "start_time": "2026-02-14T15:30:00",
  "duration": 300.5,
  "emotion_distribution": {
    "happy": 120,
    "sad": 80,
    "neutral": 100
  },
  "state_transitions": 4,
  "songs_played": 12,
  "playlist_id": "37i9dQZF1DXcBWIGoYBM5M"
}
```

### Viewing Analytics
- Session summary chart displays automatically on stop
- Browse `session/` folder for historical data
- Check Spotify for created playlists

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] Camera activates on session start
- [ ] Emotion detection updates in real-time
- [ ] Music state changes after 3s stable emotion
- [ ] Queue displays correct song count
- [ ] Spotify playback starts automatically
- [ ] Session playlist created on stop

### Unit Tests (if implemented)
```bash
python -m pytest tests/
```

---

## 🛠️ Development

### Adding New Emotion States
1. Update `emotion/detector.py` with new class
2. Add mapping in `music/state_controller.py`
3. Define audio features in `music/audio_features.py`

### Customizing Audio Features
Edit `STATE_AUDIO_FEATURES` in `music/audio_features.py`:
```python
MusicState.CUSTOM: {
    "energy": (0.5, 0.7),
    "valence": (0.4, 0.6),
    "tempo": (100, 140)
}
```

### Training Custom Models
```bash
python training/train_minixception.py --dataset FER2013 --epochs 50
```

---

## 📚 Documentation

Comprehensive guides available in `md_export/`:
- **[DOCUMENTATION_INDEX.md](md_export/DOCUMENTATION_INDEX.md)** – Navigation hub
- **[QUICK_REFERENCE.md](md_export/QUICK_REFERENCE.md)** – Quick start & tweaks
- **[DYNAMIC_QUEUE_SYSTEM.md](md_export/DYNAMIC_QUEUE_SYSTEM.md)** – Queue system deep dive
- **[ARCHITECTURE_DIAGRAMS.md](md_export/ARCHITECTURE_DIAGRAMS.md)** – Visual explanations

---

## 🤝 Contributing

Contributions welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE.md](md_export/LICENSE.md) for details.

---

## 🙏 Acknowledgments

- **FER2013 Dataset** – Facial Expression Recognition dataset
- **AffectNet** – Large-scale emotion dataset
- **Spotify Web API** – Music playback and recommendations
- **PyTorch Team** – Deep learning framework
- **OpenCV Contributors** – Computer vision library

---

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

## 🎵 Demo

Session summary example:

![Session Analytics](md_export/VISUAL_SUMMARY.md)

**Generated Playlist:**
```
Emotion Mix - 2026-02-14 15:47
├─ Happy Songs (5 tracks, 12:30)
├─ Sad Songs (4 tracks, 10:45)
└─ Neutral Songs (3 tracks, 8:20)
Total: 12 tracks, 31:35 duration
```

---

**Built with ❤️ using Python, PyTorch, and Spotify API**
