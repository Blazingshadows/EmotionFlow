import time
from music.music_state import MusicState
from config import MIN_EMOTION_STABLE_TIME, STATE_COOLDOWN

EMOTION_TO_STATE = {
    "Happy": MusicState.UPBEAT,
    "Surprise": MusicState.UPBEAT,
    "Sad": MusicState.CALM,
    "Fear": MusicState.CALM,
    "Angry": MusicState.INTENSE,
    "Neutral": MusicState.BACKGROUND,
    "Disgust": MusicState.BACKGROUND,
    "Rock": MusicState.ROCK,
}

class MusicStateController:
    def __init__(self):
        self.current_state = None
        self.last_switch_time = 0

    def update(self, emotion, stable_duration):
        now = time.time()
        target_state = EMOTION_TO_STATE.get(emotion)

        if target_state is None:
            return False, self.current_state

        if target_state != self.current_state:
            if stable_duration >= MIN_EMOTION_STABLE_TIME and \
               (now - self.last_switch_time) >= STATE_COOLDOWN:
                self.current_state = target_state
                self.last_switch_time = now
                return True, self.current_state

        return False, self.current_state
