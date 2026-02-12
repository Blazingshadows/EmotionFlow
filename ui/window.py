"""
window.py

Unified GUI:
Camera → Emotion → Stability → State → Spotify → Session → Analytics
"""

import sys
import os
import time
import threading
from collections import Counter

import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
import matplotlib.pyplot as plt

from emotion.detector import EmotionDetector
from emotion.stability import EmotionStability
from music.spotify_client import SpotifyClient
from music.state_controller import MusicStateController
from music.rolling_player import RollingPlayer
from session.analytics import SessionAnalytics
from session.session_manager import SessionManager
from config import CONFIDENCE_THRESHOLD
from emotion.gesture_detector import GestureDetector


# -----------------------------
# Utility: auto camera selection
# -----------------------------
def auto_camera_index(max_indices=3):
    for i in range(max_indices):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap is None or not cap.isOpened():
            try:
                cap.release()
            except:
                pass
            continue
        ret, _ = cap.read()
        cap.release()
        if ret:
            return i
    return None


# -----------------------------
# Main Window
# -----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emotion Driven Playlist")
        self.setGeometry(200, 100, 960, 640)

        # ---------------- UI ----------------
        self.video_label = QLabel("Camera feed will appear here")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.info_label = QLabel("Emotion: -   Confidence: -   State: -   FPS: -")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_btn = QPushButton("Start Session")
        self.start_btn.clicked.connect(self.start_session)

        self.stop_btn = QPushButton("Stop Session")
        self.stop_btn.clicked.connect(self.stop_session)
        self.stop_btn.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label, stretch=6)
        main_layout.addWidget(self.info_label, stretch=1)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # ---------------- Core System ----------------
        model_path = os.environ.get("MINIX_MODEL_PATH", "assets/minixception_torch.pth")
        self.detector = EmotionDetector(model_path=model_path)

        self.stability = EmotionStability()
        self.spotify = SpotifyClient()
        self.state_controller = MusicStateController()
        self.rolling_player = RollingPlayer(self.spotify)

        self.session_manager = SessionManager()
        self.analytics = SessionAnalytics()

        self.gesture_detector = GestureDetector()

        self.last_valid_emotion = "Neutral"
        self.last_music_state = None

        # ---------------- Camera + Timer ----------------
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        self.last_ts = time.time()
        self.fps = 0.0

        self.session_events = []

    # -------------------------
    # Session Controls
    # -------------------------
    def start_session(self):
        cam_idx = auto_camera_index(max_indices=4)
        if cam_idx is None:
            QMessageBox.warning(self, "No camera", "No working camera detected.")
            return

        self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Camera open failed", "Could not open camera.")
            return

        self.session_manager.start_session()
        self.analytics = SessionAnalytics()
        self.session_events = []

        self.timer.start(16)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.info_label.setText("Session started...")

    def stop_session(self):
        self.timer.stop()

        if self.cap:
            self.cap.release()
            self.cap = None

        self.session_manager.end_session()

        # Create session playlist and show summary
        if self.session_events:
            playlist_id = self.rolling_player.finalize_session()
            self._save_session_summary(self.session_events, playlist_id)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.info_label.setText("Session stopped. Check Spotify for your emotion mix playlist!")

    # -------------------------
    # Frame Loop
    # -------------------------
    def _update_frame(self):
        if self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # FPS calculation
        now = time.time()
        dt = now - self.last_ts if self.last_ts else 0.001
        self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
        self.last_ts = now

        # Gesture detection
        gesture_detected, gesture_conf = self.gesture_detector.detect_yo_gesture(frame)
        if gesture_detected:
            detected_emotion = "Rock"
            conf = gesture_conf
            annotated = frame.copy()
        else:
            # Emotion detection
            label, conf, annotated = self.detector.predict_frame(frame)

            # Confidence gating
            if not label or conf < CONFIDENCE_THRESHOLD:
                detected_emotion = self.last_valid_emotion
            else:
                detected_emotion = label
                self.last_valid_emotion = label

        # Stability
        stable_emotion, stable_duration = self.stability.update(detected_emotion)

        # Extra bias prevention
        if stable_emotion in ["Sad", "Fear"] and conf < 0.6:
            stable_emotion = "Neutral"

        # Music State Logic
        changed, music_state = self.state_controller.update(
            stable_emotion,
            stable_duration
        )

        if changed:
            playlist_name = self.spotify.get_playlist_name(music_state)
            print(f"[STATE CHANGE] {stable_emotion} → {music_state.value} | Playlist: {playlist_name}")
            self.rolling_player.on_state_change(music_state)
            self.last_music_state = music_state

            self.session_manager.log_event(
                "music_state_change",
                {"new_state": music_state.value}
            )

        # Session logging
        self.session_manager.log_emotion(stable_emotion, conf)
        self.analytics.update(stable_emotion, self.last_music_state)

        self.session_events.append({
            "emotion": stable_emotion,
            "confidence": conf
        })

        # UI update
        h, w, ch = annotated.shape
        bytes_per_line = ch * w
        qt_img = QImage(
            annotated.data, w, h,
            bytes_per_line,
            QImage.Format.Format_BGR888
        )

        pix = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

        self.video_label.setPixmap(pix)

        state_text = self.last_music_state.value if self.last_music_state else "-"
        queue_status = self.rolling_player.get_queue_status()
        queue_info = f" | Queue: {queue_status.get('queue_size', 0)} songs" if queue_status.get('queue_size', 0) > 0 else ""
        
        self.info_label.setText(
            f"Emotion: {stable_emotion}   "
            f"Confidence: {conf:.2f}   "
            f"State: {state_text}   "
            f"FPS: {self.fps:.1f}{queue_info}"
        )
        
        # Check if queue needs refilling
        self.rolling_player.check_and_refill_queue()

    # -------------------------
    # Session Summary Plot
    # -------------------------
    def _save_session_summary(self, events, playlist_id: str = ""):
        """
        Generate and save session summary with emotion distribution
        and link to created Spotify playlist.
        
        Args:
            events: List of emotion events from session
            playlist_id: ID of created Spotify playlist
        """
        emotions = [e["emotion"] for e in events if e["emotion"]]
        counts = Counter(emotions)

        labels = list(counts.keys())
        values = [counts[k] for k in labels]

        # Create emotion distribution chart
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(labels, values, color='steelblue', alpha=0.8)
        ax.set_xlabel("Emotion", fontsize=12, fontweight='bold')
        ax.set_ylabel("Frequency", fontsize=12, fontweight='bold')
        ax.set_title("Session Emotion Distribution", fontsize=14, fontweight='bold')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}',
                   ha='center', va='bottom', fontweight='bold')
        
        # Add queue statistics
        queue_summary = self.rolling_player.spotify.song_queue.get_session_summary()
        songs_played = queue_summary.get("total_songs_played", 0)
        total_duration = queue_summary.get("total_duration_seconds", 0) / 60.0  # Convert to minutes
        
        # Add info text
        info_text = f"Total Songs: {songs_played} | Duration: {total_duration:.1f} min"
        if playlist_id:
            info_text += f" | Playlist created!"
        
        fig.text(0.5, 0.02, info_text, ha='center', fontsize=10, style='italic')
        
        plt.tight_layout(rect=[0, 0.05, 1, 1])

        outpath = f"session_summary_{int(time.time())}.png"
        plt.savefig(outpath, dpi=200, bbox_inches='tight')
        plt.close()

        # Show summary message
        summary_msg = f"📊 Session Summary Saved\n\n"
        summary_msg += f"Emotions detected: {len(counts)}\n"
        summary_msg += f"Total songs played: {songs_played}\n"
        summary_msg += f"Duration: {total_duration:.1f} minutes\n\n"
        summary_msg += f"Chart saved: {outpath}"
        
        if playlist_id:
            summary_msg += f"\n\n✅ Spotify playlist created with {songs_played} songs!\n"
            summary_msg += "Check your Spotify library for the emotion mix playlist."
        
        QMessageBox.information(self, "Session Summary", summary_msg)

    # -------------------------
    # Cleanup
    # -------------------------
    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.session_manager.end_session()
        event.accept()


# -----------------------------
# Run app
# -----------------------------
def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
