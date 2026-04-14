# System Architecture Documentation

## Overview

This document provides comprehensive architectural diagrams and explanations for the Emotion Driven Music Recommendation System.

---

## 1. Complete System Architecture Diagram

```mermaid
graph TB
    subgraph Input["Input Layer"]
        Camera["Camera Feed<br/>(OpenCV)"]
        Gesture["Gesture Input<br/>(HandTracker)"]
    end

    subgraph Vision["Computer Vision Layer"]
        FaceDetect["Face Detection<br/>(YOLO)"]
        EmotionDet["Emotion Detection<br/>(MiniXception/MobileNetV2)"]
        GestureDet["Gesture Recognition<br/>(Yo Sign → Rock)"]
    end

    subgraph Processing["Processing Layer"]
        Confidence["Confidence Filter<br/>(Threshold: 0.5)"]
        Stability["Emotion Stability<br/>(Min: 3s stable)"]
        StateMap["State Mapping<br/>(Emotion → Music State)"]
    end

    subgraph MusicStates["Music State Engine"]
        Calm["CALM<br/>(Sad, Fear)"]
        Upbeat["UPBEAT<br/>(Happy, Surprise)"]
        Intense["INTENSE<br/>(Angry)"]
        Background["BACKGROUND<br/>(Neutral, Disgust)"]
        Rock["ROCK<br/>(Gesture)"]
    end

    subgraph MusicLogic["Music Recommendation Logic"]
        StateControl["State Controller<br/>(Cooldown: 5s)"]
        AudioMap["Audio Feature Mapping<br/>(Energy, Valence, Tempo)"]
        RollingPlayer["Rolling Player<br/>(Dynamic Queue)"]
    end

    subgraph SpotifyAPI["Spotify Integration"]
        SpotifyClient["Spotify Client<br/>(OAuth2 Auth)"]
        Search["Playlist Search<br/>(Keyword Fallback)"]
        Playback["Playback Control<br/>(Play/Pause/Skip)"]
        QueueMgmt["Queue Management<br/>(20 song buffer)"]
    end

    subgraph SessionMgmt["Session Management"]
        SessionMgr["Session Manager<br/>(Start/Stop)"]
        Analytics["Session Analytics<br/>(Emotion Time, Switches)"]
        Storage["JSON Storage<br/>(session/*.json)"]
    end

    subgraph UI["User Interface (PyQt6)"]
        VideoDisplay["Video Display<br/>(Real-time Feed)"]
        InfoPanel["Info Panel<br/>(Emotion, State, FPS)"]
        Controls["Controls<br/>(Start/Stop Session)"]
        Summary["Session Summary<br/>(Playlist Creation)"]
    end

    subgraph Training["Model Training (Offline)"]
        FER2013["FER2013 Dataset"]
        AffectNet["AffectNet Dataset"]
        TrainPipe["Training Pipeline<br/>(PyTorch)"]
        Evaluation["Model Evaluation<br/>(Confusion Matrix)"]
        Models["Trained Models<br/>(.pth files)"]
    end

    %% Flow connections
    Camera --> FaceDetect
    Gesture --> GestureDet
    FaceDetect --> EmotionDet
    EmotionDet --> Confidence
    GestureDet --> Confidence
    Confidence --> Stability
    Stability --> StateMap
    
    StateMap --> Calm
    StateMap --> Upbeat
    StateMap --> Intense
    StateMap --> Background
    StateMap --> Rock
    
    Calm --> StateControl
    Upbeat --> StateControl
    Intense --> StateControl
    Background --> StateControl
    Rock --> StateControl
    
    StateControl --> AudioMap
    AudioMap --> RollingPlayer
    RollingPlayer --> SpotifyClient
    
    SpotifyClient --> Search
    Search --> QueueMgmt
    QueueMgmt --> Playback
    Playback --> RollingPlayer
    
    StateControl --> Analytics
    Stability --> Analytics
    Analytics --> SessionMgr
    SessionMgr --> Storage
    
    FaceDetect --> VideoDisplay
    EmotionDet --> InfoPanel
    StateControl --> InfoPanel
    SessionMgr --> Controls
    SessionMgr --> Summary
    
    FER2013 --> TrainPipe
    AffectNet --> TrainPipe
    TrainPipe --> Models
    Models --> Evaluation
    Models --> EmotionDet
    
    %% Styling
    classDef inputClass fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef visionClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef processClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef stateClass fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef musicClass fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef spotifyClass fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef sessionClass fill:#ffccbc,stroke:#bf360c,stroke-width:2px
    classDef uiClass fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    classDef trainClass fill:#f8bbd0,stroke:#880e4f,stroke-width:2px
    
    class Camera,Gesture inputClass
    class FaceDetect,EmotionDet,GestureDet visionClass
    class Confidence,Stability,StateMap processClass
    class Calm,Upbeat,Intense,Background,Rock stateClass
    class StateControl,AudioMap,RollingPlayer musicClass
    class SpotifyClient,Search,Playback,QueueMgmt spotifyClass
    class SessionMgr,Analytics,Storage sessionClass
    class VideoDisplay,InfoPanel,Controls,Summary uiClass
    class FER2013,AffectNet,TrainPipe,Evaluation,Models trainClass
```

---

## 2. Simplified Data Flow Diagram

```mermaid
flowchart LR
    A[Camera Input] --> B[Face Detection]
    B --> C[Emotion Classification]
    C --> D[Confidence Check]
    D --> E[Stability Filter]
    E --> F[State Mapping]
    F --> G[Music Recommendation]
    G --> H[Spotify Playback]
    
    E --> I[Session Analytics]
    F --> I
    I --> J[JSON Storage]
    
    style A fill:#e3f2fd
    style C fill:#fff3e0
    style E fill:#f3e5f5
    style G fill:#fff9c4
    style H fill:#c8e6c9
    style I fill:#ffccbc
```

---

## 3. Layered Architecture

```mermaid
graph TB
    subgraph L1["Layer 1: Presentation Layer"]
        UI1["PyQt6 GUI"]
        UI2["Video Display"]
        UI3["Controls & Info"]
    end
    
    subgraph L2["Layer 2: Application Layer"]
        APP1["Session Manager"]
        APP2["State Controller"]
        APP3["Rolling Player"]
    end
    
    subgraph L3["Layer 3: Business Logic Layer"]
        BL1["Emotion Detection"]
        BL2["Stability Filter"]
        BL3["Audio Feature Mapping"]
        BL4["Song Queue Manager"]
    end
    
    subgraph L4["Layer 4: Integration Layer"]
        INT1["Spotify API Client"]
        INT2["Session Analytics"]
        INT3["Storage Manager"]
    end
    
    subgraph L5["Layer 5: Infrastructure Layer"]
        INF1["OpenCV"]
        INF2["PyTorch Models"]
        INF3["File System"]
        INF4["Spotipy Library"]
    end
    
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> L5
    
    style L1 fill:#e0f2f1
    style L2 fill:#fff9c4
    style L3 fill:#f3e5f5
    style L4 fill:#c8e6c9
    style L5 fill:#ffccbc
```

---

## 4. Real-time Processing Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Camera
    participant Detector
    participant Stability
    participant StateCtrl
    participant Spotify
    participant UI
    
    User->>UI: Start Session
    UI->>Camera: Initialize
    
    loop Every Frame (60 FPS)
        Camera->>Detector: Video Frame
        Detector->>Detector: Face Detection (YOLO)
        Detector->>Detector: Emotion Classification
        Detector->>Stability: Emotion + Confidence
        
        alt Confidence > 0.5
            Stability->>StateCtrl: Stable Emotion (3s)
            StateCtrl->>StateCtrl: Check Cooldown (5s)
            
            alt State Change Allowed
                StateCtrl->>Spotify: New Music State
                Spotify->>Spotify: Search Songs
                Spotify->>Spotify: Update Queue
                Spotify->>Spotify: Start Playback
                Spotify-->>UI: Update Status
            end
        end
        
        Detector->>UI: Update Video Display
        StateCtrl-->>UI: Update Info Panel
    end
    
    User->>UI: Stop Session
    UI->>Spotify: Create Playlist
    UI->>User: Show Summary
```

---

## 5. Component Interaction Diagram

```mermaid
graph LR
    subgraph Core["Core Components"]
        ED[Emotion Detector]
        SC[State Controller]
        RP[Rolling Player]
    end
    
    subgraph External["External Services"]
        SP[Spotify API]
        FS[File System]
    end
    
    subgraph Support["Support Modules"]
        ST[Stability Filter]
        AF[Audio Features]
        SQ[Song Queue]
        AN[Analytics]
    end
    
    ED <--> ST
    ED --> SC
    SC <--> RP
    SC --> AN
    
    RP --> AF
    AF --> SQ
    SQ --> SP
    RP <--> SP
    
    AN --> FS
    
    style Core fill:#fff3e0
    style External fill:#c8e6c9
    style Support fill:#f3e5f5
```

---

## 6. Module Dependency Graph

```mermaid
graph TD
    A[app.py] --> B[ui/window.py]
    
    B --> C[emotion/detector.py]
    B --> D[emotion/stability.py]
    B --> E[emotion/gesture_detector.py]
    B --> F[music/state_controller.py]
    B --> G[music/rolling_player.py]
    B --> H[music/spotify_client.py]
    B --> I[session/session_manager.py]
    B --> J[session/analytics.py]
    
    C --> K[emotion/face_utils.py]
    
    F --> L[music/music_state.py]
    
    G --> H
    G --> M[music/song_queue.py]
    
    H --> L
    H --> N[music/audio_features.py]
    H --> M
    
    N --> L
    
    I --> O[session/*.json]
    
    style A fill:#e1f5ff
    style B fill:#e0f2f1
    style C fill:#fff3e0
    style D fill:#fff3e0
    style E fill:#fff3e0
    style F fill:#fff9c4
    style G fill:#fff9c4
    style H fill:#c8e6c9
    style I fill:#ffccbc
    style J fill:#ffccbc
```

---

## 7. Emotion to Music Mapping Flow

```mermaid
flowchart TD
    Start([Detected Emotion]) --> Check{Confidence > 0.5?}
    
    Check -->|No| Prev[Use Previous Emotion]
    Check -->|Yes| Stable{Stable for 3s?}
    
    Prev --> Stable
    Stable -->|No| Wait[Keep Monitoring]
    Stable -->|Yes| Map[Map to Music State]
    
    Map --> S1{Which Emotion?}
    
    S1 -->|Happy/Surprise| MS1[UPBEAT State]
    S1 -->|Sad/Fear| MS2[CALM State]
    S1 -->|Angry| MS3[INTENSE State]
    S1 -->|Neutral/Disgust| MS4[BACKGROUND State]
    S1 -->|Yo Gesture| MS5[ROCK State]
    
    MS1 --> Cool{Cooldown OK?}
    MS2 --> Cool
    MS3 --> Cool
    MS4 --> Cool
    MS5 --> Cool
    
    Cool -->|No| Wait2[Wait for Cooldown]
    Cool -->|Yes| Features[Map Audio Features]
    
    Features --> AF1[Energy: 0.6-1.0]
    Features --> AF2[Valence: 0.6-1.0]
    Features --> AF3[Tempo: 120-180]
    
    AF1 --> Search[Search Spotify]
    AF2 --> Search
    AF3 --> Search
    
    Search --> Queue[Add to Queue]
    Queue --> Play[Start Playback]
    
    Play --> End([Music Playing])
    
    Wait --> Start
    Wait2 --> Start
    
    style Start fill:#e1f5ff
    style Map fill:#f3e5f5
    style MS1 fill:#e8f5e9
    style MS2 fill:#e8f5e9
    style MS3 fill:#e8f5e9
    style MS4 fill:#e8f5e9
    style MS5 fill:#e8f5e9
    style Search fill:#c8e6c9
    style Play fill:#c8e6c9
    style End fill:#e0f2f1
```

---

## Architecture Design Principles

### 1. **Modular Design**
- Each component (emotion, music, session, UI) is self-contained
- Clear interfaces between modules
- Easy to test and maintain

### 2. **Real-time Processing**
- 60 FPS camera processing
- Efficient emotion detection pipeline
- Asynchronous Spotify API calls

### 3. **Stability Mechanisms**
- Confidence threshold (0.5) to filter uncertain predictions
- Emotion stability timer (3 seconds) to avoid rapid switches
- State cooldown (5 seconds) to prevent music disruption

### 4. **Fault Tolerance**
- Fallback to keyword search if playlist fails
- Graceful handling of camera errors
- Session recovery and logging

### 5. **Extensibility**
- Support for multiple emotion detection models
- Pluggable music state mappings
- Configurable audio feature targets

---

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Deep Learning** | PyTorch, MiniXception, MobileNetV2 |
| **Computer Vision** | OpenCV, YOLO, MediaPipe |
| **Music API** | Spotify Web API, Spotipy |
| **UI Framework** | PyQt6 |
| **Data Storage** | JSON (session logs) |
| **Authentication** | OAuth2 (Spotify) |
| **Language** | Python 3.x |

---

## System Requirements

### Hardware
- Webcam (720p or higher recommended)
- CPU: Dual-core 2.0 GHz minimum
- RAM: 4GB minimum (8GB recommended)
- Internet connection for Spotify API

### Software
- Python 3.8+
- Windows/Linux/macOS
- Spotify Premium account (for playback control)

---

## Performance Characteristics

| Metric | Value |
|--------|-------|
| **Emotion Detection Latency** | < 50ms per frame |
| **Processing Frame Rate** | 60 FPS |
| **Model Accuracy** | 74.71% (AffectNet validation) |
| **State Switch Latency** | 3-8 seconds (stability + cooldown) |
| **Queue Buffer Size** | 20 songs |
| **Session Storage** | JSON (avg 200KB per session) |

---

## Key Features

1. **Multi-modal Input**: Camera + gesture recognition
2. **Dual Model Support**: MiniXception (lightweight) and MobileNetV2 (accurate)
3. **Intelligent State Management**: Stability filtering and cooldown
4. **Audio Feature Matching**: Maps emotions to musical characteristics
5. **Session Analytics**: Tracks emotional patterns and transitions
6. **Dynamic Playlist Generation**: Creates personalized playlists from sessions
7. **Real-time Visualization**: Live emotion display and confidence scores

---

## Future Enhancement Opportunities

- Multi-user support with face recognition
- Cloud-based session synchronization
- Advanced music recommendation using collaborative filtering
- Integration with additional music streaming services
- Mobile application support
- Voice command integration
- Emotion trend prediction using LSTM/Transformer models
