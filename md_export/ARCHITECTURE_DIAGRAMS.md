# System Architecture Diagram

## 🏗️ Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMOTION DRIVEN MUSIC SYSTEM                   │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       INPUT LAYER                                 │
├──────────────────────────────────────────────────────────────────┤
│  Webcam → Face Detection → CNN Emotion Prediction                │
│  (emotion/detector.py)                                            │
│                                                                    │
│  Output: emotion_label, confidence                               │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                    STABILITY LAYER                                │
├──────────────────────────────────────────────────────────────────┤
│  Input: Raw emotion + confidence                                 │
│  (emotion/stability.py)                                           │
│                                                                    │
│  ├─ Track emotion over 15-frame window                           │
│  ├─ Calculate stable_emotion and duration                        │
│  └─ Output: stable_emotion, stable_duration (seconds)            │
│                                                                    │
│  Only stable emotions trigger state changes                      │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                    STATE CONTROLLER LAYER                         │
├──────────────────────────────────────────────────────────────────┤
│  Input: stable_emotion, stable_duration                          │
│  (music/state_controller.py)                                     │
│                                                                    │
│  ├─ Map emotion → MusicState                                     │
│  │  Happy → UPBEAT                                               │
│  │  Sad → CALM                                                   │
│  │  Angry → INTENSE                                              │
│  │  Neutral → BACKGROUND                                         │
│  │  Rock → ROCK                                                  │
│  │                                                                │
│  ├─ Check stability duration (≥3 sec)                            │
│  ├─ Check cooldown since last change (≥5 sec)                   │
│  └─ Output: state_changed, new_state                             │
│                                                                    │
│  Only change when both conditions met                            │
└──────────────────────────────────────────────────────────────────┘
                                ↓
        ┌───────────────────────┴───────────────────────┐
        │ State Changed?                                 │
        ├────────────┬──────────────────────────────────┤
        │ NO: Do     │ YES: Trigger Rolling Player      │
        │ nothing    │                                   │
        └────────────┴──────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                  ROLLING PLAYER LAYER                             │
├──────────────────────────────────────────────────────────────────┤
│  Input: MusicState                                               │
│  (music/rolling_player.py)                                       │
│                                                                    │
│  on_state_change(state)                                          │
│  ├─ Queue songs for this state (background thread)              │
│  └─ Trigger queue_songs_for_state()                             │
│                                                                    │
│  check_and_refill_queue()                                        │
│  ├─ Check queue_size < threshold                                │
│  ├─ If yes: Add 3 more songs                                    │
│  └─ Keep playback continuous                                    │
│                                                                    │
│  finalize_session()                                              │
│  ├─ Collect all played songs                                    │
│  └─ Create Spotify playlist                                     │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                  SONG DISCOVERY LAYER                             │
├──────────────────────────────────────────────────────────────────┤
│  Input: MusicState, count=5                                      │
│  (music/spotify_client.py :: queue_songs_for_state)             │
│                                                                    │
│  ├─ Get seed playlist for state                                 │
│  │  UPBEAT → "37i9dQZF1EVJHK7Q1TBABQ"                           │
│  │  CALM → "37i9dQZF1EIfTmpqlGn32s"                             │
│  │  etc.                                                          │
│  │                                                                │
│  ├─ Fetch 50 tracks from seed playlist                          │
│  └─ Get audio features via Spotify API                          │
│                                                                    │
│  For each track:                                                 │
│  ├─ Get: energy, valence, danceability, tempo, acousticness     │
│  ├─ Compare vs STATE_AUDIO_FEATURES[state]                      │
│  ├─ Calculate match score (0.0 to 1.0)                          │
│  ├─ Sort by score (highest first)                               │
│  └─ Return top 5 songs                                          │
│                                                                    │
│  Output: List[Song] with best matches                           │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                   QUEUE MANAGEMENT LAYER                          │
├──────────────────────────────────────────────────────────────────┤
│  Input: List[Song], MusicState                                   │
│  (music/song_queue.py & music/spotify_client.py)                │
│                                                                    │
│  ├─ Add songs to SongQueue                                      │
│  ├─ Add songs to Spotify playback queue                         │
│  ├─ Track all songs in history                                  │
│  └─ Monitor queue depth                                         │
│                                                                    │
│  Queue State:                                                     │
│  [Current] [Next] [Next] [Next] [Next]                          │
│   Playing   Ready  Ready  Ready  Ready                           │
│                                                                    │
│  When queue < 2:                                                │
│  ├─ Refill with 3 more songs                                    │
│  └─ No silence or interruption                                  │
│                                                                    │
│  Output: Songs playing continuously                             │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                 PLAYBACK & SPOTIFY LAYER                          │
├──────────────────────────────────────────────────────────────────┤
│  Input: Song URIs from queue                                     │
│  (music/spotify_client.py)                                       │
│                                                                    │
│  ├─ Connect to Spotify Web API                                  │
│  ├─ Find active device                                          │
│  ├─ Start/queue tracks                                          │
│  ├─ Monitor playback                                            │
│  └─ Create playlist at session end                              │
│                                                                    │
│  Spotify API Calls:                                             │
│  ├─ sp.search() - Find songs                                    │
│  ├─ sp.audio_features() - Get track features                   │
│  ├─ sp.add_to_queue() - Add to playback queue                  │
│  ├─ sp.start_playback() - Begin playing                        │
│  ├─ sp.user_playlist_create() - Create playlist                │
│  └─ sp.playlist_add_items() - Add tracks to playlist           │
│                                                                    │
│  Output: Music playing, playlist created                        │
└──────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────┐
│                      OUTPUT/UI LAYER                              │
├──────────────────────────────────────────────────────────────────┤
│  (ui/window.py)                                                  │
│                                                                    │
│  Display:                                                         │
│  ├─ Live webcam feed with face detection                        │
│  ├─ Current emotion & confidence                                │
│  ├─ Current music state                                         │
│  ├─ Queue size (real-time)                                      │
│  ├─ FPS counter                                                  │
│  └─ Session summary with:                                       │
│     ├─ Emotion distribution chart                               │
│     ├─ Total songs played                                       │
│     ├─ Total duration                                           │
│     └─ Spotify playlist link                                    │
│                                                                    │
│  User Controls:                                                   │
│  ├─ Start Session (begin webcam + music)                        │
│  └─ Stop Session (save summary + create playlist)               │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagram

```
REAL-TIME FRAME LOOP (every ~16ms)
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  for frame in video_stream:                                      │
│  ├─ Detect face (face_cascade)                                  │
│  ├─ Extract & preprocess (48x48 grayscale)                      │
│  ├─ Run CNN (MiniXception)                                      │
│  │  └─ Output: emotion_label, confidence                        │
│  │                                                                │
│  ├─ Stability buffer (15-frame window)                          │
│  │  └─ Output: stable_emotion, stable_duration                  │
│  │                                                                │
│  ├─ State controller                                            │
│  │  ├─ Check: duration >= 3s AND cooldown >= 5s                │
│  │  ├─ If YES: new_state = EMOTION_TO_STATE[emotion]          │
│  │  └─ If state changed: trigger rolling_player                │
│  │                                                                │
│  ├─ Update analytics                                            │
│  │  └─ Track emotion_time, state_time, transitions             │
│  │                                                                │
│  └─ Update UI                                                   │
│     └─ Display: emotion, confidence, state, queue_size          │
│                                                                    │
│  BACKGROUND (triggered on state change):                        │
│  ├─ on_state_change(state)                                      │
│  │  └─ Threading daemon: queue_songs_for_state()               │
│  │     ├─ search_songs_by_state(state, count=5)               │
│  │     │  ├─ Get seed playlist                                 │
│  │     │  ├─ Fetch 50 tracks                                   │
│  │     │  ├─ Get audio features (API call)                     │
│  │     │  ├─ Score tracks (0.0-1.0)                            │
│  │     │  └─ Return top 5                                      │
│  │     │                                                        │
│  │     └─ queue_songs_for_state()                              │
│  │        ├─ Add to SongQueue                                  │
│  │        └─ Add to Spotify queue (API call)                   │
│  │                                                                │
│  └─ check_and_refill_queue()                                    │
│     ├─ Check: queue_size < 2                                   │
│     └─ If YES: queue 3 more songs (background)                 │
│                                                                    │
│  SESSION END:                                                     │
│  └─ finalize_session()                                          │
│     └─ create_session_playlist()                                │
│        ├─ Get all played songs from SongQueue                  │
│        ├─ Create playlist via Spotify API                      │
│        └─ Add all songs to playlist                            │
│                                                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 State Machine Diagram

```
                    EMOTION → STATE MAPPING
                    
                    Emotion Detected
                           ↓
                    ┌──────────────┐
                    │ Raw Emotion  │  e.g., "Happy"
                    └──────┬───────┘
                           ↓
                    ┌──────────────────────┐
                    │ Stability Buffer     │  15-frame window
                    │ (Smooth Jitter)      │
                    └──────┬───────────────┘
                           ↓
              Emotion Stable For 3+ Seconds?
              ├─ No  → Wait, keep same state
              └─ Yes → Check cooldown
                       ↓
          Cooldown (5s) Since Last Change?
          ├─ No  → Wait, keep same state
          └─ Yes → Proceed to map
                   ↓
          ┌──────────────────────────────────────┐
          │ EMOTION_TO_STATE MAPPING             │
          ├──────────────────────────────────────┤
          │ Happy       → UPBEAT                 │
          │ Surprise    → UPBEAT                 │
          │ Sad         → CALM                   │
          │ Fear        → CALM                   │
          │ Angry       → INTENSE                │
          │ Neutral     → BACKGROUND             │
          │ Disgust     → BACKGROUND             │
          │ Rock(Gesture)→ ROCK                  │
          └──────────┬───────────────────────────┘
                     ↓
          New State ≠ Current State?
          ├─ No  → No change, keep queuing current state
          └─ Yes → STATE_CHANGED = True
                   ↓
          ┌─────────────────────────────────┐
          │ on_state_change(new_state)      │
          │                                  │
          │ ├─ Queue 2-5 songs for          │
          │ │  new_state                    │
          │ │                                │
          │ ├─ Add to Spotify queue          │
          │ │  (no interruption)             │
          │ │                                │
          │ └─ Update current_state          │
          └──────────┬────────────────────────┘
                     ↓
          Music transitions to new emotion
          when current song finishes
```

---

## 🔄 Queue Refilling Cycle

```
QUEUE MONITORING (every frame check)

Current Queue: [Song1] [Song2] [Song3] [Song4]
                Play    Ready   Ready   Ready
                ↓        ↓       ↓       ↓
              Playing at X position
              
              
Time passes...
Song1 ends, Song2 starts playing


Queue: [Song2] [Song3] [Song4]
        Play    Ready   Ready
        
Queue size = 3 → OK, don't refill (threshold = 2)


Time passes...
Song2 ends, Song3 starts playing


Queue: [Song3] [Song4]
        Play    Ready
        
Queue size = 2 → OK, at threshold


Time passes...
Song3 ends, Song4 starts playing


Queue: [Song4]
        Play
        
Queue size = 1 → BELOW THRESHOLD! REFILL!
        ↓
        check_and_refill_queue()
        ├─ Search for 3 new songs (same emotion state)
        ├─ Add to SongQueue
        ├─ Add to Spotify queue
        └─ Return
        
        ↓
        
Queue: [Song4] [New1] [New2] [New3]
        Play    Ready  Ready  Ready
        
Queue size = 4 → OK again


... Music continues without interruption ...
```

---

## 🎵 Audio Feature Scoring

```
INPUT: Track with features
┌─────────────────────────────────────────┐
│ Song: "Blinding Lights"                 │
│ Energy: 0.73                            │
│ Valence: 0.81                           │
│ Danceability: 0.80                      │
│ Tempo: 174                              │
│ Acousticness: 0.006                     │
└─────────────────────────────────────────┘
                 ↓
           Target State: UPBEAT
           
┌─────────────────────────────────────────┐
│ STATE_AUDIO_FEATURES[UPBEAT]:           │
│ Energy: (0.6, 1.0)                      │
│ Valence: (0.6, 1.0)                     │
│ Danceability: (0.6, 1.0)                │
│ Tempo: (120, 180)                       │
└─────────────────────────────────────────┘
                 ↓
           SCORING ALGORITHM
           
Score Energy:
  Target: 0.6-1.0
  Actual: 0.73
  ✓ Within range → Score: 1.0
  
Score Valence:
  Target: 0.6-1.0
  Actual: 0.81
  ✓ Within range → Score: 1.0
  
Score Danceability:
  Target: 0.6-1.0
  Actual: 0.80
  ✓ Within range → Score: 1.0
  
Score Tempo:
  Target: 120-180 BPM
  Actual: 174 BPM
  ✓ Within range → Score: 1.0
  
FINAL SCORE = (1.0 + 1.0 + 1.0 + 1.0) / 4 = 1.0 (Perfect Match!)
                 ↓
        ┌────────────────────┐
        │ Rank: 1st Place    │
        │ Score: 1.0 / 1.0   │
        │ Queue: YES ✓       │
        └────────────────────┘
```

---

## 📈 Session Timeline Example

```
TIME    EMOTION      STABLE?  STATE        ACTION
────────────────────────────────────────────────────────────
0:00    NEUTRAL      No       -            Start session
0:05    HAPPY        No       -            
0:10    HAPPY        No       -            
0:15    HAPPY        Yes      UPBEAT       ← 3s stable!
        
        [Background Thread]
        ├─ Search UPBEAT songs
        ├─ Get audio features
        ├─ Score & rank
        ├─ Queue 5 songs
        └─ Start playback
        
0:20    HAPPY        Yes      UPBEAT       Song 1 playing
        QUEUE: [1*][2][3][4][5]
        
1:00    HAPPY        Yes      UPBEAT       Song 3 playing
        QUEUE: [3*][4][5][6][7]
        (auto-refilled after 2)
        
1:45    SAD          No       UPBEAT       Emotion changing...
1:50    SAD          No       UPBEAT       
1:55    SAD          Yes      CALM         ← 3s stable!
        
        [Background Thread]
        ├─ Search CALM songs
        ├─ Get audio features
        ├─ Score & rank
        └─ Queue 5 CALM songs
        
2:00    SAD          Yes      CALM         Song 5 (UPBEAT) still playing
        QUEUE: [5*UPBEAT][8CALM][9][10][11]
        
2:15    SAD          Yes      CALM         Song 8 (CALM) starts
        ← Natural transition!
        
3:00    SAD          Yes      CALM         Song 10 playing
        (queue refilled)
        
5:00                          -            User stops session
        
        [Main Thread]
        ├─ Get all played songs: [1,2,3,4,5,6,7,8,9,10,11,12]
        ├─ States: 7 UPBEAT + 5 CALM
        ├─ Create Spotify playlist
        ├─ Add 12 songs
        └─ Show summary
```

---

## 🧩 Component Dependencies

```
┌──────────────────────────────────────────────────────┐
│                   UI LAYER                           │
│              (ui/window.py)                          │
└────────────┬──────────────────────────────────────┬──┘
             │                                      │
             ↓                                      ↓
    ┌──────────────────┐              ┌──────────────────────┐
    │ EmotionDetector  │              │ RollingPlayer        │
    │ (emotion/        │              │ (music/rolling_      │
    │  detector.py)    │              │  player.py)          │
    └────────┬─────────┘              └────────┬─────────────┘
             │                                 │
             ↓                                 ↓
    ┌──────────────────┐              ┌──────────────────────┐
    │ EmotionStability │              │ MusicStateController │
    │ (emotion/        │              │ (music/state_        │
    │  stability.py)   │              │  controller.py)      │
    └────────┬─────────┘              └────────┬─────────────┘
             │                                 │
             └─────────────┬───────────────────┘
                           ↓
                ┌──────────────────────┐
                │ SpotifyClient        │
                │ (music/spotify_      │
                │  client.py)          │
                │                      │
                ├─ search_songs()      │
                ├─ queue_songs()       │
                ├─ play()              │
                └─ create_playlist()   │
                           │
        ┌──────────────────┴───────────────────┐
        │                                      │
        ↓                                      ↓
    ┌──────────────────┐            ┌──────────────────┐
    │ AudioFeatures    │            │ SongQueue        │
    │ (music/audio_    │            │ (music/song_     │
    │  features.py)    │            │  queue.py)       │
    │                  │            │                  │
    │ - State targets  │            │ - Song storage   │
    │ - Feature        │            │ - History track  │
    │   matching       │            │ - Statistics     │
    │ - Scoring        │            └──────────────────┘
    └──────────────────┘
        │
        ↓
    Spotify Web API
```

---

That's it! These diagrams show the complete system architecture from multiple perspectives. 🎵✨
