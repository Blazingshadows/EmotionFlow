# Architecture Diagrams for Research Paper

This document contains publication-ready diagrams suitable for inclusion in academic research papers.

---

## Figure 1: High-Level System Architecture

```mermaid
graph TB
    subgraph A["Input Module"]
        A1[Webcam Feed<br/>60 FPS]
        A2[Gesture Input<br/>Hand Tracking]
    end
    
    subgraph B["Vision Module"]
        B1[YOLO Face<br/>Detection]
        B2[CNN Emotion<br/>Classification<br/>7 Classes]
        B3[Gesture<br/>Recognition]
    end
    
    subgraph C["Emotion Processing"]
        C1[Confidence<br/>Threshold<br/>θ = 0.5]
        C2[Temporal<br/>Stability<br/>τ = 3s]
        C3[State<br/>Mapping]
    end
    
    subgraph D["Music Recommendation"]
        D1[Music State<br/>Engine<br/>5 States]
        D2[Audio Feature<br/>Extraction<br/>Energy, Valence, Tempo]
        D3[Spotify<br/>Integration]
    end
    
    subgraph E["Session & Analytics"]
        E1[Session<br/>Manager]
        E2[Analytics<br/>Engine]
        E3[Persistent<br/>Storage]
    end
    
    A1 --> B1
    A2 --> B3
    B1 --> B2
    B2 --> C1
    B3 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> D1
    D1 --> D2
    D2 --> D3
    
    C2 --> E2
    D1 --> E2
    E2 --> E1
    E1 --> E3
    
    style A fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style B fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style C fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style D fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style E fill:#ffebee,stroke:#c62828,stroke-width:2px
```

**Caption**: *System architecture showing the five main modules: (1) Input acquisition, (2) Computer vision processing, (3) Emotion processing with temporal stability, (4) Music recommendation engine, and (5) Session management and analytics.*

---

## Figure 2: Emotion Detection Pipeline

```mermaid
flowchart LR
    A[Video Frame<br/>224×224×3] --> B[YOLO<br/>Face Detector]
    B --> C{Face<br/>Detected?}
    C -->|Yes| D[ROI<br/>Extraction]
    C -->|No| Z[Skip Frame]
    D --> E[CNN Model<br/>MobileNetV2]
    E --> F[Softmax<br/>Layer]
    F --> G[Emotion<br/>+ Confidence]
    G --> H{Conf > 0.5?}
    H -->|Yes| I[Accepted]
    H -->|No| J[Use Previous]
    I --> K[Output]
    J --> K
    
    style A fill:#e3f2fd
    style E fill:#fff3e0
    style G fill:#c8e6c9
    style K fill:#e0f2f1
```

**Caption**: *Emotion detection pipeline showing frame preprocessing, face detection using YOLO, emotion classification using MobileNetV2 CNN, and confidence-based filtering (θ = 0.5).*

---

## Figure 3: Emotion-to-Music State Mapping

```mermaid
graph LR
    subgraph Emotions["Detected Emotions"]
        E1[Happy<br/>Surprise]
        E2[Sad<br/>Fear]
        E3[Angry]
        E4[Neutral<br/>Disgust]
        E5[Yo Gesture]
    end
    
    subgraph States["Music States"]
        S1[UPBEAT<br/>Energy: 0.6-1.0<br/>Valence: 0.6-1.0<br/>Tempo: 120-180]
        S2[CALM<br/>Energy: 0.0-0.4<br/>Valence: 0.0-0.5<br/>Tempo: 60-100]
        S3[INTENSE<br/>Energy: 0.7-1.0<br/>Valence: 0.3-0.8<br/>Tempo: 140-200]
        S4[BACKGROUND<br/>Energy: 0.2-0.5<br/>Valence: 0.3-0.7<br/>Tempo: 80-120]
        S5[ROCK<br/>Energy: 0.7-1.0<br/>Valence: 0.4-0.9<br/>Tempo: 120-200]
    end
    
    E1 ==> S1
    E2 ==> S2
    E3 ==> S3
    E4 ==> S4
    E5 ==> S5
    
    style E1 fill:#fff59d
    style E2 fill:#b2ebf2
    style E3 fill:#ef9a9a
    style E4 fill:#e0e0e0
    style E5 fill:#ce93d8
    
    style S1 fill:#a5d6a7
    style S2 fill:#90caf9
    style S3 fill:#ef5350
    style S4 fill:#bdbdbd
    style S5 fill:#9575cd
```

**Caption**: *Mapping between detected emotions and music states with corresponding audio feature ranges. Each music state defines target ranges for energy, valence, and tempo used in Spotify API queries.*

---

## Figure 4: Temporal Stability Mechanism

```mermaid
sequenceDiagram
    participant Frame as Video Frame
    participant Detector as Emotion Detector
    participant Stability as Stability Filter
    participant Controller as State Controller
    participant Music as Music Player
    
    Note over Frame,Music: t = 0s
    Frame->>Detector: Frame 1 (Happy)
    Detector->>Stability: Happy, conf=0.8
    Stability->>Stability: Start timer (Happy)
    
    Note over Frame,Music: t = 1.5s
    Frame->>Detector: Frame N (Happy)
    Detector->>Stability: Happy, conf=0.75
    Stability->>Stability: Continue timer (1.5s)
    
    Note over Frame,Music: t = 3.0s (Stability Reached)
    Frame->>Detector: Frame M (Happy)
    Detector->>Stability: Happy, conf=0.82
    Stability->>Controller: Stable: Happy (3s)
    Controller->>Controller: Check cooldown
    
    alt Cooldown Passed (5s)
        Controller->>Music: Switch to UPBEAT
        Music-->>Controller: ✓ State Changed
    else Cooldown Active
        Controller->>Controller: Ignore request
    end
```

**Caption**: *Temporal stability mechanism showing how emotions must remain consistent for τ = 3 seconds before triggering a music state change. State transitions also respect a cooldown period of 5 seconds to prevent frequent disruptions.*

---

## Figure 5: Music Recommendation Algorithm Flow

```mermaid
flowchart TD
    Start([Stable Emotion]) --> Map[Map to Music State]
    Map --> Features[Define Audio Features<br/>Energy, Valence, Tempo]
    Features --> Search{Search Type}
    
    Search -->|Primary| Playlist[Query State Playlist<br/>Spotify API]
    Search -->|Fallback| Keyword[Keyword Search<br/>State Name]
    
    Playlist --> Check{Results?}
    Keyword --> Check
    
    Check -->|Yes| Score[Calculate Feature<br/>Match Score]
    Check -->|No| Keyword
    
    Score --> Rank[Rank by Score]
    Rank --> Select[Select Top N Songs<br/>N = 5]
    Select --> Queue[Add to Queue<br/>Buffer Size = 20]
    Queue --> Play{Queue<br/>Management}
    
    Play -->|Play| Playback[Start Playback<br/>Spotify SDK]
    Play -->|Skip| Next[Next Song]
    Play -->|Full| Remove[Remove Oldest]
    
    Playback --> Monitor[Monitor Playback]
    Monitor --> End([Continuous Music])
    
    style Start fill:#e3f2fd
    style Features fill:#fff3e0
    style Score fill:#f3e5f5
    style Queue fill:#c8e6c9
    style Playback fill:#e8f5e9
```

**Caption**: *Music recommendation algorithm flow showing playlist-based search with keyword fallback, audio feature matching, scoring, and dynamic queue management with a buffer size of 20 songs.*

---

## Figure 6: Model Architecture Comparison

```mermaid
graph TB
    subgraph Mini["MiniXception Architecture"]
        M1[Input: 48×48×1<br/>Grayscale]
        M2[Conv Block 1<br/>32 filters]
        M3[Residual Block<br/>64 filters]
        M4[Residual Block<br/>128 filters]
        M5[Global Avg Pool]
        M6[Dense Layer<br/>7 classes]
        
        M1 --> M2 --> M3 --> M4 --> M5 --> M6
    end
    
    subgraph Mobile["MobileNetV2 Architecture"]
        MB1[Input: 224×224×3<br/>RGB]
        MB2[Inverted Residual<br/>Bottleneck Blocks<br/>17 layers]
        MB3[Conv 1×1<br/>1280 filters]
        MB4[Global Avg Pool]
        MB5[Custom Classifier<br/>7 classes]
        
        MB1 --> MB2 --> MB3 --> MB4 --> MB5
    end
    
    M6 -.-> Comp[Performance Comparison]
    MB5 -.-> Comp
    
    Comp --> T1[MiniXception:<br/>Parameters: ~600K<br/>Speed: 15ms/frame<br/>Accuracy: ~68%]
    Comp --> T2[MobileNetV2:<br/>Parameters: ~3.5M<br/>Speed: 35ms/frame<br/>Accuracy: 74.71%]
    
    style Mini fill:#fff3e0
    style Mobile fill:#e8f5e9
    style T1 fill:#ffccbc
    style T2 fill:#c8e6c9
```

**Caption**: *Comparison of two CNN architectures used for emotion classification. MiniXception offers faster inference suitable for resource-constrained environments, while MobileNetV2 provides higher accuracy with acceptable latency for real-time processing.*

---

## Figure 7: Session Analytics Data Structure

```mermaid
classDiagram
    class Session {
        +string session_id
        +string start_time
        +string end_time
        +List~EmotionEvent~ emotion_history
        +List~MusicEvent~ music_history
        +Dictionary summary
        +save_to_json()
    }
    
    class EmotionEvent {
        +string emotion
        +float confidence
        +string timestamp
    }
    
    class MusicEvent {
        +string track_name
        +string artist
        +string state
        +float energy
        +float valence
        +int tempo
        +string timestamp
    }
    
    class Analytics {
        +float duration
        +Dictionary emotion_distribution
        +Dictionary state_distribution
        +int state_switches
        +calculate_metrics()
        +generate_plots()
    }
    
    Session "1" --> "*" EmotionEvent
    Session "1" --> "*" MusicEvent
    Session "1" --> "1" Analytics
```

**Caption**: *UML class diagram showing the session data structure. Each session records emotion events with confidence scores, music playback events with audio features, and aggregated analytics for post-session analysis.*

---

## Figure 8: System Performance Metrics

```mermaid
graph LR
    subgraph Latency["System Latency Breakdown"]
        L1[Frame Capture<br/>~5ms]
        L2[Face Detection<br/>~15ms]
        L3[Emotion Classification<br/>~35ms]
        L4[Processing Logic<br/>~5ms]
        L5[Total Latency<br/>~60ms]
        
        L1 --> L2 --> L3 --> L4 --> L5
    end
    
    subgraph Accuracy["Model Accuracy"]
        A1[Overall: 74.71%]
        A2[Happy: 84.73%]
        A3[Sad: 87.48%]
        A4[Angry: 72.47%]
        A5[Neutral: 64.51%]
    end
    
    style Latency fill:#e3f2fd
    style Accuracy fill:#e8f5e9
    style L5 fill:#ffab91
    style A2 fill:#a5d6a7
    style A3 fill:#a5d6a7
```

**Caption**: *System performance metrics showing (left) latency breakdown for the emotion detection pipeline achieving real-time processing at ~60ms per frame, and (right) per-class accuracy from the MobileNetV2 model trained on AffectNet dataset.*

---

## Table 1: Emotion Classification Performance

| Emotion | Precision | Recall | F1-Score | Support |
|---------|-----------|--------|----------|---------|
| Angry | 0.6880 | 0.7247 | 0.7059 | 712 |
| Disgust | 0.6946 | 0.7767 | 0.7334 | 618 |
| Fear | 0.7006 | 0.6756 | 0.6879 | 672 |
| **Happy** | **0.8597** | **0.8473** | **0.8534** | 622 |
| **Sad** | **0.8793** | **0.8748** | **0.8771** | 791 |
| Surprise | 0.6777 | 0.6381 | 0.6573 | 514 |
| Neutral | 0.6959 | 0.6451 | 0.6695 | 603 |
| **Overall** | **0.7476** | **0.7471** | **0.7467** | **4532** |

---

## Table 2: Music State Audio Feature Ranges

| Music State | Energy | Valence | Tempo (BPM) | Typical Emotions |
|-------------|--------|---------|-------------|------------------|
| CALM | 0.0 - 0.4 | 0.0 - 0.5 | 60 - 100 | Sad, Fear |
| BACKGROUND | 0.2 - 0.5 | 0.3 - 0.7 | 80 - 120 | Neutral, Disgust |
| UPBEAT | 0.6 - 1.0 | 0.6 - 1.0 | 120 - 180 | Happy, Surprise |
| INTENSE | 0.7 - 1.0 | 0.3 - 0.8 | 140 - 200 | Angry |
| ROCK | 0.7 - 1.0 | 0.4 - 0.9 | 120 - 200 | Yo Gesture |

---

## Table 3: System Configuration Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Confidence Threshold (θ) | 0.5 | Minimum confidence for emotion acceptance |
| Stability Time (τ) | 3 seconds | Required duration for stable emotion |
| State Cooldown | 5 seconds | Minimum time between state changes |
| Queue Buffer Size | 20 songs | Maximum songs in recommendation queue |
| Processing Frame Rate | 60 FPS | Target frame processing rate |
| Input Resolution | 224×224 | CNN input image size |
| Emotion Classes | 7 | Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral |
| Music States | 5 | CALM, BACKGROUND, UPBEAT, INTENSE, ROCK |

---

## Usage in LaTeX

To include these diagrams in your research paper, you can:

1. **Render Mermaid to PNG/SVG**: Use online tools like [Mermaid Live Editor](https://mermaid.live) or the VS Code Mermaid extension
2. **Include in LaTeX**:
```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.9\textwidth]{figures/system_architecture.png}
    \caption{High-level system architecture showing the five main modules.}
    \label{fig:architecture}
\end{figure}
```

3. **Reference in text**: `As shown in Figure \ref{fig:architecture}, the system comprises five main modules...`

---

## Citation Suggestion

If referencing this architecture in academic work:

```bibtex
@software{emotion_music_system,
  title={Emotion Driven Music Recommendation System},
  author={[Your Name]},
  year={2026},
  description={Real-time emotion detection and music recommendation using deep learning and Spotify API}
}
```
