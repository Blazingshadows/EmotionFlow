import threading

class RollingPlayer:
    def __init__(self, spotify_client):
        self.spotify = spotify_client
        self.auto_mode = True

    def on_state_change(self, state):
        if self.auto_mode:
            # Run in background thread to avoid blocking UI
            thread = threading.Thread(target=self.spotify.play_state, args=(state,), daemon=True)
            thread.start()

    def set_auto_mode(self, enabled: bool):
        self.auto_mode = enabled
