import time
class EmotionStability:
    def __init__(self):
        self.current_emotion = None
        self.start_time = None

    def update(self, emotion):
        now = time.time()

        if emotion != self.current_emotion:
            self.current_emotion = emotion
            self.start_time = now

        stable_duration = now - self.start_time
        return self.current_emotion, stable_duration