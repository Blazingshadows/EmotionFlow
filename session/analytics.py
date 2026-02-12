import time
from collections import defaultdict

class SessionAnalytics:
    def __init__(self):
        self.start_time = time.time()
        self.last_time = self.start_time
        self.emotion_time = defaultdict(float)
        self.state_time = defaultdict(float)
        self.last_emotion = None
        self.last_state = None
        self.state_switches = 0

    def update(self, emotion, state):
        now = time.time()
        dt = now - self.last_time

        if self.last_emotion:
            self.emotion_time[self.last_emotion] += dt
        if self.last_state:
            self.state_time[self.last_state] += dt

        if state != self.last_state:
            self.state_switches += 1

        self.last_emotion = emotion
        self.last_state = state
        self.last_time = now

    def summary(self):
        return {
            "duration": time.time() - self.start_time,
            "emotion_distribution": dict(self.emotion_time),
            "state_distribution": dict(self.state_time),
            "state_switches": self.state_switches
        }
