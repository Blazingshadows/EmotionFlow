# Dynamic Queue-Based Playback System

## Overview

Instead of abruptly switching between static Spotify playlists when emotions change, the system now maintains a dynamic song queue that:

1. **Queues 2-5 songs** when an emotion becomes stable
2. **Smoothly transitions** when emotions change mid-playback
3. **Refills the queue** as songs finish playing
4. **Creates a session playlist** at the end with all mixed emotions

---

## How It Works

### Stage 1: Emotion Becomes Stable
- User's emotion is detected and becomes stable for ≥3 seconds
- System identifies the target `MusicState` (CALM, UPBEAT, INTENSE, BACKGROUND, ROCK)
- `rolling_player.on_state_change(state)` is triggered

### Stage 2: Song Discovery & Queuing
- `SpotifyClient.queue_songs_for_state(state)` searches for 2-5 songs
- Uses **audio feature matching** to find songs that fit the emotional state
- Songs are scored by how well they match:
  - **Energy**: How intense/powerful the song is
  - **Valence**: How happy/sad the song is
  - **Danceability**: How rhythmic/danceable it is
  - **Tempo**: BPM (beats per minute)
  - **Acousticness**: Acoustic vs. electronic production

### Stage 3: Smooth Playback
- First song starts playing immediately
- Remaining songs are **added to Spotify queue** automatically
- Queue refills every ~2-3 songs if emotion stays the same
- If emotion changes → new songs added to queue for that state

### Stage 4: Emotion Change During Playback
- If emotion changes during song 3 or later
- New 2-5 songs are queued for the new emotion
- No interruption—natural transition after current song ends
- Creates a **smooth blend** of different emotional songs

### Stage 5: Session End
- All played songs are collected
- A **new Spotify playlist** is created with all songs
- Named: `"Emotion Mix - YYYY-MM-DD HH:MM"`
- Contains complete emotion journey of the session

---

## Audio Feature Targets

Each `MusicState` has audio feature ranges that songs must match:

### CALM (Sad/Fear)
- Energy: 0.0–0.4 (low)
- Valence: 0.0–0.5 (sad)
- Danceability: 0.0–0.5 (not danceable)
- Tempo: 60–100 BPM (slow)

### BACKGROUND (Neutral/Disgust)
- Energy: 0.2–0.5 (low-medium)
- Valence: 0.3–0.7 (neutral)
- Danceability: 0.3–0.6 (slightly danceable)
- Tempo: 80–120 BPM

### UPBEAT (Happy/Surprise)
- Energy: 0.6–1.0 (high)
- Valence: 0.6–1.0 (very happy)
- Danceability: 0.6–1.0 (very danceable)
- Tempo: 120–180 BPM (fast)

### INTENSE (Angry)
- Energy: 0.7–1.0 (very high)
- Valence: 0.3–0.8 (mixed)
- Danceability: 0.5–1.0 (danceable)
- Tempo: 140–200 BPM (very fast)

### ROCK (Gesture)
- Energy: 0.7–1.0
- Valence: 0.4–0.9
- Danceability: 0.4–0.8
- Tempo: 120–200 BPM

---

## Key Components

### 1. `music/audio_features.py`
Defines audio feature targets and scoring algorithm.

**Key Functions:**
- `get_audio_feature_query(state)` - Build filter for Spotify
- `calculate_feature_score(track_features, state)` - Score how well track matches state

### 2. `music/song_queue.py`
Manages the queue of upcoming songs and history.

**Key Classes:**
- `Song` - Individual track with metadata
- `SongQueue` - Queue manager with thread-safe operations

**Key Methods:**
- `add_songs(songs, state)` - Add songs to queue
- `get_next_songs(count)` - Peek at upcoming songs
- `pop_song()` - Get and remove next song
- `get_session_summary()` - Summary of all songs played

### 3. `music/spotify_client.py` (Enhanced)
Added dynamic song selection capabilities.

**New Methods:**
- `search_songs_by_state(state, count)` - Find songs matching state
- `queue_songs_for_state(state, count)` - Queue songs (2-5)
- `_add_queued_songs_to_playback(songs)` - Add to Spotify queue
- `create_session_playlist(name)` - Create playlist from session

### 4. `music/rolling_player.py` (Enhanced)
Orchestrates smooth transitions.

**New Methods:**
- `on_state_change(state)` - Queue songs when emotion changes
- `check_and_refill_queue()` - Maintain queue during playback
- `finalize_session()` - Create session playlist
- `get_queue_status()` - Get queue info for UI

### 5. `ui/window.py` (Enhanced)
Updated to show queue status and create playlist.

**Changes:**
- Queue size displayed in real-time
- `_save_session_summary()` now includes:
  - Total songs played
  - Total duration
  - Spotify playlist link
  - Enhanced visualization

---

## User Experience Flow

```
1. User starts session
   ↓
2. System detects emotion (e.g., "Happy")
   ↓
3. Emotion becomes stable for 3 seconds
   ↓
4. System queues 2-5 UPBEAT songs
   ↓
5. First song plays, rest queued
   ↓
6. User's emotion changes to "Sad" during song 3
   ↓
7. System queues 2-5 CALM songs
   ↓
8. After current song: CALM songs play (smooth transition)
   ↓
9. If emotion stays SAD: Queue refilled with CALM songs
   ↓
10. If emotion changes to "Angry": INTENSE songs queued
   ↓
11. User ends session
    ↓
12. Spotify playlist created with all songs: 
    "Emotion Mix - Happy (2), Sad (4), Angry (3)"
```

---

## Configuration

In `config.py`:
```python
# Emotion stability
MIN_EMOTION_STABLE_TIME = 3    # Seconds before queuing new songs

# Music state control
STATE_COOLDOWN = 5             # Cooldown before state change
```

In `music/audio_features.py`:
Edit `STATE_AUDIO_FEATURES` dict to adjust what songs match each emotion.

---

## Technical Details

### Audio Feature Matching Algorithm

For each track, the system:

1. Fetches its audio features from Spotify
2. Compares against the target state's feature ranges
3. Calculates a match score (0.0 to 1.0)
4. Ranks tracks by score
5. Returns top N tracks

**Scoring Logic:**
- If feature is within target range: score = 1.0
- If outside range: score decreases based on distance
- Final score = average of all feature scores

### Queue Refilling Strategy

System checks queue before each frame:
- If queue < 2 songs AND emotion unchanged
- Auto-queue 3 more songs
- Keeps playback continuous

### Thread Safety

`SongQueue` uses threading locks to safely:
- Add songs from background thread
- Read queue from main UI thread
- Prevent race conditions

---

## Benefits

✅ **Smooth Transitions** - No jarring playlist switches  
✅ **Continuous Music** - Queue always has songs ready  
✅ **Audio Feature Matching** - Songs actually fit the emotion  
✅ **Session Replay** - Spotify playlist preserves emotion journey  
✅ **Real-Time Adaptation** - Responds immediately to emotion changes  
✅ **Thread-Safe** - No blocking or race conditions  

---

## Example Session

**Timeline:**
```
00:00 - Session starts, emotion: NEUTRAL
        Queue: [Background song 1-3]
        
00:15 - Emotion changes to HAPPY (stable)
        Queue: [Background 2-3, Upbeat 1-5]
        
01:00 - Emotion still HAPPY
        Background songs ended, now playing Upbeat
        Queue refilled: [Upbeat 2-5, new Upbeat 1-2]
        
01:45 - Emotion changes to SAD (stable)
        Queue: [Upbeat 3-5, Calm 1-5]
        
02:30 - Emotion still SAD
        Queue refilled: [Calm 2-5, new Calm 1-2]
        
03:00 - Session ends
        Spotify creates: "Emotion Mix - 2026-02-12 15:30"
        Songs: 3 Background + 7 Upbeat + 6 Calm = 16 total
```

**Spotify Playlist Result:**
```
Emotion Mix - 2026-02-12 15:30
├─ [BACKGROUND] Song 1 (4:12)
├─ [BACKGROUND] Song 2 (3:45)
├─ [BACKGROUND] Song 3 (3:58)
├─ [UPBEAT] Song 4 (3:32)
├─ [UPBEAT] Song 5 (4:01)
├─ ... (7 total Upbeat)
├─ [CALM] Song 12 (4:15)
├─ ... (6 total Calm)
└─ Total: 51 minutes, 16 songs
```

User can now replay their emotional journey anytime! 🎵

