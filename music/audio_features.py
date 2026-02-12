"""
Audio Feature Mappings for Music State

Maps emotional states to Spotify audio feature targets for song selection.
Uses audio features: energy, valence, danceability, acousticness, tempo
"""

from music.music_state import MusicState

# Audio feature targets for each emotion state
# Format: (energy, valence, danceability, acousticness, min_tempo, max_tempo)
STATE_AUDIO_FEATURES = {
    MusicState.CALM: {
        "energy": (0.0, 0.4),          # Low energy
        "valence": (0.0, 0.5),         # Low positivity
        "danceability": (0.0, 0.5),    # Low danceability
        "acousticness": (0.0, 1.0),    # Any (allows both acoustic and ambient)
        "tempo": (60, 100),            # Slow tempo
    },
    
    MusicState.BACKGROUND: {
        "energy": (0.2, 0.5),
        "valence": (0.3, 0.7),
        "danceability": (0.3, 0.6),
        "acousticness": (0.0, 1.0),
        "tempo": (80, 120),
    },
    
    MusicState.UPBEAT: {
        "energy": (0.6, 1.0),          # High energy
        "valence": (0.6, 1.0),         # High positivity (happy)
        "danceability": (0.6, 1.0),    # High danceability
        "acousticness": (0.0, 0.5),    # Less acoustic, more electronic
        "tempo": (120, 180),           # Fast tempo
    },
    
    MusicState.INTENSE: {
        "energy": (0.7, 1.0),          # Very high energy
        "valence": (0.3, 0.8),         # Mixed valence (can be angry or passionate)
        "danceability": (0.5, 1.0),    # High danceability
        "acousticness": (0.0, 0.3),    # Mostly electronic/produced
        "tempo": (140, 200),           # Very fast tempo
    },
    
    MusicState.ROCK: {
        "energy": (0.7, 1.0),
        "valence": (0.4, 0.9),         # Can be sad or energetic
        "danceability": (0.4, 0.8),
        "acousticness": (0.0, 0.4),    # Mix of acoustic and electric
        "tempo": (120, 200),           # Varies
    }
}


def get_audio_feature_query(state: MusicState) -> str:
    """
    Build Spotify search query based on audio feature targets.
    Returns a filter string for use in Spotify API.
    
    Args:
        state: MusicState enum value
        
    Returns:
        Query string with audio feature filters
    """
    if state not in STATE_AUDIO_FEATURES:
        return ""
    
    features = STATE_AUDIO_FEATURES[state]
    
    # Build Spotify Audio Features filter
    # Format: audio_features(energy:0.3-0.7, valence:0.5-1.0, etc.)
    parts = []
    
    # Energy filter
    energy_min, energy_max = features["energy"]
    parts.append(f"energy:{energy_min}-{energy_max}")
    
    # Valence (positivity) filter
    valence_min, valence_max = features["valence"]
    parts.append(f"valence:{valence_min}-{valence_max}")
    
    # Danceability filter
    dance_min, dance_max = features["danceability"]
    parts.append(f"danceability:{dance_min}-{dance_max}")
    
    return " ".join(parts)


def calculate_feature_score(track_features: dict, state: MusicState) -> float:
    """
    Calculate how well a track matches the target state's audio features.
    Score ranges from 0.0 to 1.0 (higher = better match).
    
    Args:
        track_features: Dict with keys: energy, valence, danceability, acousticness, tempo
        state: Target MusicState
        
    Returns:
        Match score (0.0 to 1.0)
    """
    if state not in STATE_AUDIO_FEATURES:
        return 0.0
    
    targets = STATE_AUDIO_FEATURES[state]
    scores = []
    
    # Score each feature
    feature_keys = ["energy", "valence", "danceability"]
    
    for key in feature_keys:
        if key in track_features and key in targets:
            feature_val = track_features[key]
            target_min, target_max = targets[key]
            
            # If within range, score = 1.0, else penalize
            if target_min <= feature_val <= target_max:
                scores.append(1.0)
            else:
                # Distance from target range
                if feature_val < target_min:
                    distance = (target_min - feature_val) / (target_min + 0.1)
                else:
                    distance = (feature_val - target_max) / (1.0 - target_max + 0.1)
                scores.append(max(0.0, 1.0 - distance))
    
    # Tempo scoring
    if "tempo" in track_features:
        track_tempo = track_features["tempo"]
        tempo_min, tempo_max = targets["tempo"]
        
        if tempo_min <= track_tempo <= tempo_max:
            scores.append(1.0)
        else:
            distance = abs(track_tempo - (tempo_min + tempo_max) / 2) / 100.0
            scores.append(max(0.0, 1.0 - distance * 0.5))
    
    return sum(scores) / len(scores) if scores else 0.0
