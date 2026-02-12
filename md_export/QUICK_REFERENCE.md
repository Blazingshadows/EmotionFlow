# Quick Reference - Dynamic Queue System

## 🚀 Quick Start

**No setup needed!** The system is automatically integrated.

Just run your session normally:
```bash
python app.py
```

The dynamic queue system works automatically:
1. ✅ Emotion detected → becomes stable
2. ✅ Songs queued for that emotion
3. ✅ First song plays, rest queued
4. ✅ Emotion changes → new songs queued
5. ✅ Session ends → Spotify playlist created

---

## 📊 What You'll See

### During Session (UI)
```
Emotion: Happy   Confidence: 0.87   State: UPBEAT   FPS: 28.4 | Queue: 4 songs
```

Queue indicator shows songs remaining and will refill automatically.

### In Console (Logs)
```
[Queue] Added 5 songs for UPBEAT
[Spotify] Found 5 songs for UPBEAT
[Spotify] ✓ Now playing: Song Name - Artist Name
[Spotify] Queued: Song Name 2 - Artist
[RollingPlayer] Queue updated for UPBEAT
```

### At Session End (Message)
```
📊 Session Summary Saved

Emotions detected: 3
Total songs played: 12
Duration: 8.5 minutes

Chart saved: session_summary_1707...
✅ Spotify playlist created with 12 songs!
Check your Spotify library for the emotion mix playlist.
```

---

## 🎛️ Quick Tweaks

### Make It Queue More Songs
In `music/rolling_player.py`, line ~15:
```python
self.min_queue_threshold = 2    # ← Change to 4 for more padding
```

### Make Emotions Less Strict
In `music/audio_features.py`, find `UPBEAT` (line ~30):
```python
"energy": (0.6, 1.0),     # ← Change to (0.5, 1.0) for more songs
```

### Make Playlist Names Custom
In `music/spotify_client.py`, line ~105:
```python
playlist_name = f"Emotion Session - {timestamp}"  # ← Customize here
```

---

## 🐛 Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| **No music plays** | Open Spotify app (need active device) |
| **Queue stays empty** | Check internet connection |
| **No playlist created** | Check Spotify account permissions |
| **Songs don't match emotion** | Adjust `STATE_AUDIO_FEATURES` ranges |
| **Queue never refills** | Increase `min_queue_threshold` |

---

## 📈 Monitoring Queue

### During Session (Terminal)
Watch console for queue messages:
```bash
[Queue] Added 5 songs for UPBEAT
[Queue] Now playing: Blinding Lights - The Weeknd
[RollingPlayer] Queue running low, refilling...
```

### Check Queue Programmatically
```python
status = rolling_player.get_queue_status()
print(f"Queue: {status['queue_size']} songs")
print(f"Current state: {status['current_state']}")
print(f"Total played: {status['songs_played']}")
```

---

## 🎵 Audio Features Explained

**Why we use audio features:**
- Songs have measurable properties
- We can match emotions to properties
- Results are predictable and consistent

**The 5 Key Features:**

| Feature | Range | Emotion Match |
|---------|-------|---------------|
| **Energy** | 0.0-1.0 | Happy=High, Sad=Low |
| **Valence** | 0.0-1.0 | Happy=High, Angry=Mid, Sad=Low |
| **Danceability** | 0.0-1.0 | Upbeat=High, Calm=Low |
| **Tempo (BPM)** | 0-250 | Fast=Happy/Angry, Slow=Sad |
| **Acousticness** | 0.0-1.0 | Varies (both work) |

---

## 🔄 How Songs Get Queued

```
1. Emotion Stable
   ↓
2. Get target state (UPBEAT, CALM, etc)
   ↓
3. Search Spotify for 50 candidate songs
   ↓
4. Get audio features for each
   ↓
5. Score each (0.0-1.0):
   - Does energy match? How close?
   - Does valence match? How close?
   - Does danceability match?
   - Does tempo match?
   ↓
6. Average the scores
   ↓
7. Pick top 2-5 songs
   ↓
8. Add to queue
   ↓
9. Add to Spotify playback queue
```

---

## 📋 Session Playlist

### What Gets Included
✅ **All songs played**  
✅ **In order they played**  
✅ **With emotion state tracked**  

### Playlist Location
Spotify → Search → "Emotion Mix - 2026-02-12 15:47"

### Use Cases
- 📱 Listen to your emotion journey
- 📊 Share with friends
- 🎓 Study your patterns
- 🎵 Use for future sessions

---

## 🧮 Expected Session Stats

**Typical 10-minute session:**
- Songs played: 8-12
- Emotions: 2-4 changes
- Queue refills: 3-5 times
- Playlist size: ~50 minutes of music

---

## 💡 Pro Tips

### Tip 1: Smooth Transitions
System automatically queues 2-5 songs per emotion, so transitions are smooth!

### Tip 2: Let It Stabilize
Don't change expressions too fast. Give ~3 seconds for emotion to stabilize before songs queue.

### Tip 3: Active Device Required
Have Spotify open on your computer/phone. Queue needs an active device to add songs.

### Tip 4: Check the Logs
Console shows what's happening:
```bash
[Queue] Added 5 songs for UPBEAT
[RollingPlayer] Queue running low, refilling...
[Spotify] ✓ Added 9 songs to playlist
```

### Tip 5: Customize Features
Don't like the songs? Edit `STATE_AUDIO_FEATURES` to be more strict or lenient.

---

## 🚨 Common Issues & Fixes

### Songs Play For Wrong Emotion
**Problem:** Emotion says UPBEAT but calm songs play  
**Fix:** Check audio feature ranges aren't too loose
```python
# In music/audio_features.py, make more strict:
"energy": (0.7, 1.0),      # Was (0.6, 1.0)
```

### Queue Never Refills
**Problem:** "Queue: 0 songs" stays in UI  
**Fix:** Check if emotion is changing too fast
```python
# In config.py, increase minimum:
MIN_EMOTION_STABLE_TIME = 5    # Was 3
```

### Spotify Says No Device
**Problem:** "[Spotify] ✗ No devices found"  
**Fix:** Open Spotify app on your computer
```bash
# Then in Python terminal:
spotify_client._get_device()  # Will find it now
```

### Playlist Never Created
**Problem:** "✗ Cannot create playlist"  
**Fix:** Check OAuth scopes in `.env`
```bash
# Run setup again:
python oauth_setup.py
```

---

## 📞 Support Commands

```python
# Check queue size
print(rolling_player.get_queue_status())

# Force queue refill
rolling_player.check_and_refill_queue()

# Get session summary
summary = spotify_client.song_queue.get_session_summary()
print(f"Played {summary['total_songs_played']} songs")

# Get all played songs
songs = spotify_client.song_queue.get_played_songs()
for song in songs:
    print(f"{song.name} by {song.artist}")

# Create playlist manually
playlist_id = spotify_client.create_session_playlist("My Emotions")
print(f"Created playlist: {playlist_id}")
```

---

## 🎓 Learning Resources

### Understand Audio Features
- Read: `DYNAMIC_QUEUE_SYSTEM.md` → "Audio Feature Targets" section
- Example: How UPBEAT emotions map to high energy/valence/danceability

### Understand Song Scoring
- Read: `music/audio_features.py` → `calculate_feature_score()` function
- See: How each feature contributes to final score

### Understand Queue Management
- Read: `music/song_queue.py` → Comments explain each method
- See: Thread-safe operations with locks

### Understand Playback Flow
- Read: `music/rolling_player.py` → Method documentation
- See: How emotion change triggers queue update

---

## 📊 Monitoring & Analytics

### Real-Time Queue Monitoring
```python
import time

while session_active:
    status = rolling_player.get_queue_status()
    print(f"State: {status['current_state']} | Queue: {status['queue_size']}")
    time.sleep(2)
```

### Session Stats After
```python
summary = spotify_client.song_queue.get_session_summary()

print(f"Session Summary:")
print(f"  Total Songs: {summary['total_songs_played']}")
print(f"  Duration: {summary['total_duration_seconds']/60:.1f} minutes")
print(f"  Songs Per State:")
for state, count in summary['songs_per_state'].items():
    print(f"    {state.value}: {count} songs")
```

---

## ✨ What's Happening Under the Hood

When you run a session:

1. **Emotion Detected** → `detector.predict_frame()`
2. **Stabilized** → `stability.update()`
3. **State Changed** → `state_controller.update()`
4. **Queue Triggered** → `rolling_player.on_state_change()`
5. **Songs Found** → `spotify_client.search_songs_by_state()`
6. **Songs Queued** → `spotify_client.queue_songs_for_state()`
7. **Queue Refilled** → `rolling_player.check_and_refill_queue()`
8. **Session Ends** → `rolling_player.finalize_session()`
9. **Playlist Created** → `spotify_client.create_session_playlist()`

All of this happens automatically! ✨

---

**Need more help?** Check the full docs:
- `DYNAMIC_QUEUE_SYSTEM.md` - Complete system explanation
- `QUEUE_SYSTEM_GUIDE.md` - Implementation and testing
- Code comments in `music/` folder
