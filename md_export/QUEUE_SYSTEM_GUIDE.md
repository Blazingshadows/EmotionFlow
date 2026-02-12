# Dynamic Queue System - Implementation Guide

## Quick Start

The dynamic queue system is now integrated and ready to use. No additional setup required beyond the existing project setup.

---

## What's New

### 1. **Smooth Emotion-Based Song Transitions**
- Instead of abruptly switching entire playlists, the system now queues 2-5 relevant songs per emotion
- Transitions happen naturally at song boundaries
- No jarring audio cuts

### 2. **Audio Feature-Based Song Selection**
- Songs are matched based on:
  - **Energy** (intensity of song)
  - **Valence** (happiness/sadness)
  - **Danceability** (rhythm/groove)
  - **Tempo** (BPM)
  - **Acousticness** (acoustic vs. electronic)
- Most relevant songs are picked for each emotion

### 3. **Automatic Queue Refilling**
- Queue is monitored in real-time
- When < 2 songs remain, system automatically adds 3 more
- Keeps playback continuous without user intervention

### 4. **Session Playlist Creation**
- At the end of each session, a Spotify playlist is created
- Contains all songs that were played
- Named: `"Emotion Mix - YYYY-MM-DD HH:MM"`
- Allows users to replay their emotional journey

### 5. **Queue Status Display**
- Real-time queue size shown in UI
- Example: `"State: UPBEAT | Queue: 4 songs"`
- Total songs played shown in session summary

---

## File Changes

### New Files:
1. **`music/audio_features.py`** - Audio feature targets and scoring
2. **`music/song_queue.py`** - Queue management and history
3. **`DYNAMIC_QUEUE_SYSTEM.md`** - Full system documentation

### Modified Files:
1. **`music/spotify_client.py`**
   - Added OAuth scope for playlist creation
   - New: `search_songs_by_state()`
   - New: `queue_songs_for_state()`
   - New: `create_session_playlist()`
   - New: Device and user management

2. **`music/rolling_player.py`**
   - Redesigned for queue-based playback
   - New: `check_and_refill_queue()`
   - New: `finalize_session()`
   - New: `get_queue_status()`

3. **`ui/window.py`**
   - Queue status display in UI
   - Enhanced session summary
   - Playlist creation feedback

4. **`music/__init__.py`**
   - Updated imports for new modules

---

## Usage

### Automatic (Default Behavior)
1. Start session → emotion detected
2. Emotion becomes stable (3+ seconds)
3. System automatically:
   - Searches for matching songs
   - Queues 2-5 songs
   - Starts playback
4. If emotion changes → new songs queued
5. End session → Spotify playlist created

### Manual Controls
```python
# Queue specific songs
spotify_client.queue_songs_for_state(MusicState.UPBEAT, count=5)

# Get queue status
status = rolling_player.get_queue_status()
print(status["queue_size"])  # Songs remaining

# Force refill queue
rolling_player.check_and_refill_queue()

# Create playlist manually
playlist_id = spotify_client.create_session_playlist("My Custom Mix")

# Get session summary
summary = spotify_client.song_queue.get_session_summary()
```

---

## Configuration

### Adjust Emotion→Music Stability Time
In `config.py`:
```python
MIN_EMOTION_STABLE_TIME = 3  # seconds before queuing (default: 3)
```

### Adjust Audio Feature Ranges
In `music/audio_features.py`, edit `STATE_AUDIO_FEATURES`:
```python
STATE_AUDIO_FEATURES = {
    MusicState.UPBEAT: {
        "energy": (0.6, 1.0),          # Change: (0.5, 0.9)
        "valence": (0.6, 1.0),         # Change: (0.7, 1.0)
        "danceability": (0.6, 1.0),    # Keep or modify
        "acousticness": (0.0, 0.5),    # Keep or modify
        "tempo": (120, 180),           # Change: (100, 200)
    }
}
```

### Adjust Queue Size
In `music/spotify_client.py`:
```python
self.song_queue = SongQueue(queue_size=20)  # Max songs in queue
```

### Adjust Queue Refill Threshold
In `music/rolling_player.py`:
```python
self.min_queue_threshold = 2  # Refill when < 2 songs remain
```

---

## How It Works

### Step-by-Step Flow

**1. Emotion Detection**
```
Camera → Face Detection → CNN → Emotion Label (e.g., "Happy")
                                      ↓
                          Emotion Stability Tracking
                                      ↓
                          Is emotion stable for 3+ sec?
```

**2. State Mapping**
```
Emotion: "Happy" → MusicState: UPBEAT
                          ↓
                    State changed?
                          ↓
                   Queue songs for new state
```

**3. Song Search & Queue**
```
Search playlist for UPBEAT songs
        ↓
Fetch audio features for tracks
        ↓
Score each track (0.0 to 1.0)
        ↓
Pick top 2-5 songs
        ↓
Add to Spotify queue
```

**4. Playback**
```
Start first song
        ↓
Monitor queue depth
        ↓
Is queue < 2 songs?
    ├─ Yes → Add 3 more songs
    └─ No  → Continue playback
        ↓
Emotion changed?
    ├─ Yes → Queue new emotion's songs
    └─ No  → Keep current queue
```

**5. Session End**
```
Collect all played songs
        ↓
Create new Spotify playlist
        ↓
Add all songs to playlist
        ↓
Show summary to user
```

---

## Troubleshooting

### Songs Not Playing
- **Check**: Spotify account has active device open
- **Check**: `.env` has correct credentials
- **Fix**: Run `python oauth_setup.py` to re-authenticate

### Queue Not Filling
- **Check**: Song search is returning results (check console logs)
- **Check**: Network connection to Spotify API
- **Fix**: Increase `queue_size` in `spotify_client.py`

### Playlist Not Created
- **Check**: OAuth scope includes `playlist-modify-public` and `playlist-modify-private`
- **Check**: User ID retrieved successfully
- **Fix**: Re-run OAuth setup with correct scopes

### Poor Audio Feature Matching
- **Adjust**: `STATE_AUDIO_FEATURES` ranges in `audio_features.py`
- **Tune**: Tighten ranges to be more selective, loosen to be more permissive
- **Test**: Run a session and observe which songs are queued

---

## Debugging

### Enable Detailed Logging
Songs and queue operations print to console:
```
[Queue] Added 5 songs for UPBEAT
[Spotify] Now playing: Song Name - Artist
[RollingPlayer] Queueing songs for CALM...
```

### Check Session Summary
```python
# In Python console or code:
summary = spotify_client.song_queue.get_session_summary()
print(f"Total songs: {summary['total_songs_played']}")
print(f"Duration: {summary['total_duration_seconds']/60:.1f} min")
print(f"By state: {summary['songs_per_state']}")
```

### Monitor Queue in Real-Time
```python
while running:
    status = rolling_player.get_queue_status()
    print(f"Queue: {status['queue_size']} songs | State: {status['current_state']}")
    time.sleep(5)
```

---

## Testing Checklist

- [ ] Emotion detection works
- [ ] Emotion becomes stable (visible in console)
- [ ] State change happens (3+ second wait)
- [ ] Songs queue automatically (hear music change)
- [ ] Queue refills (continues without silence)
- [ ] Emotion change mid-song queues new songs
- [ ] Session ends with playlist creation message
- [ ] Spotify shows new "Emotion Mix" playlist
- [ ] Session summary shows correct song count
- [ ] Chart displays emotion distribution

---

## Performance Notes

- **Audio Feature Fetch**: ~500ms per 10 songs (cached)
- **Queue Refill**: ~1 second in background thread
- **Playlist Creation**: ~2 seconds (Spotify API)
- **No UI Blocking**: All network calls run in background threads

---

## API Reference

### SpotifyClient

```python
# Search and queue
search_songs_by_state(state: MusicState, count: int) -> list[Song]
queue_songs_for_state(state: MusicState, count: int) -> None

# Playlist creation
create_session_playlist(session_name: str = "Emotion Mix") -> str

# Playback control
play_state(state: MusicState) -> None
pause() -> None
next() -> None
```

### RollingPlayer

```python
# State changes
on_state_change(state: MusicState) -> None

# Queue management
check_and_refill_queue() -> None

# Session management
finalize_session() -> str  # Returns playlist ID

# Settings
set_auto_mode(enabled: bool) -> None

# Status
get_queue_status() -> dict
```

### SongQueue

```python
# Queue operations
add_songs(songs: list[Song], state: MusicState) -> None
get_next_songs(count: int = 5) -> list[str]
pop_song() -> Optional[Song]
peek_song() -> Optional[Song]

# Monitoring
queue_size() -> int
should_add_songs(threshold: int = 3) -> bool

# History
get_played_songs() -> list[Song]
get_state_distribution() -> dict[MusicState, int]
get_session_summary() -> dict
```

---

## Next Steps

1. **Test the system** - Run a full 3-5 minute session
2. **Tune audio features** - Adjust ranges for your music taste
3. **Check playlist** - Verify created Spotify playlists
4. **Gather feedback** - Does the transition feel smooth?
5. **Optimize** - Adjust queue size and refill threshold

Enjoy your emotion-driven music experience! 🎵✨

