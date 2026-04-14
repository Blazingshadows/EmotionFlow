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
    QVBoxLayout, QHBoxLayout, QMessageBox, QComboBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QTimer, Qt
import matplotlib.pyplot as plt

from emotion.detector import EmotionDetector
from emotion.detector_mobilenet import EmotionDetectorMobileNet
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

        self.model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        self.model_combo.addItem("MobileNetV2 (AffectNet)", "mobilenet")
        self.model_combo.addItem("MiniXception (FER2013)", "minixception")

        self.start_btn = QPushButton("Start Session")
        self.start_btn.clicked.connect(self.start_session)

        self.stop_btn = QPushButton("Stop Session")
        self.stop_btn.clicked.connect(self.stop_session)
        self.stop_btn.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch(1)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label, stretch=6)
        main_layout.addLayout(model_layout)
        main_layout.addWidget(self.info_label, stretch=1)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # ---------------- Core System ----------------
        detector_backend = os.environ.get("EMOTION_MODEL_BACKEND", "mobilenet").lower()
        self._loading_model = True
        combo_idx = self.model_combo.findData(detector_backend)
        if combo_idx >= 0:
            self.model_combo.setCurrentIndex(combo_idx)

        self.detector = None
        self.detector_backend = ""
        self._load_detector(detector_backend, show_message=False)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        self._loading_model = False

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
        self.is_shutting_down = False

    def _make_detector(self, backend: str):
        if backend == "mobilenet":
            model_path = os.environ.get("MOBILENET_MODEL_PATH", "checkpoints_affectnet_yolo/mobilenetv2_best.pth")
            detector = EmotionDetectorMobileNet(model_path=model_path)
            print(f"[UI] Using MobileNet detector: {model_path}")
            return detector

        model_path = os.environ.get("MINIX_MODEL_PATH", "assets/minixception_torch.pth")
        detector = EmotionDetector(model_path=model_path)
        print(f"[UI] Using MiniXception detector: {model_path}")
        return detector

    def _load_detector(self, backend: str, show_message: bool = True):
        fallback = "minixception" if backend == "mobilenet" else "mobilenet"
        try:
            self.detector = self._make_detector(backend)
            self.detector_backend = backend
        except Exception as e:
            QMessageBox.warning(
                self,
                "Model Load Failed",
                f"Failed to load {backend}: {e}\nTrying fallback model: {fallback}."
            )
            self.detector = self._make_detector(fallback)
            self.detector_backend = fallback
            fallback_idx = self.model_combo.findData(fallback)
            if fallback_idx >= 0:
                self.model_combo.setCurrentIndex(fallback_idx)

        self.last_valid_emotion = "Neutral"
        self.stability = EmotionStability()
        if show_message:
            mode_name = "MobileNetV2" if self.detector_backend == "mobilenet" else "MiniXception"
            self.info_label.setText(f"Switched model to {mode_name}. Start/continue session for comparison.")

    def _on_model_changed(self, _index: int):
        if getattr(self, "_loading_model", False):
            return
        selected_backend = self.model_combo.currentData()
        if not selected_backend or selected_backend == self.detector_backend:
            return
        self._load_detector(selected_backend, show_message=True)

    # -------------------------
    # Session Controls
    # -------------------------
    def start_session(self):
        print("\n[UI] ▶ START SESSION clicked")
        self.is_shutting_down = False
        
        cam_idx = auto_camera_index(max_indices=4)
        if cam_idx is None:
            print("[UI] ✗ No camera found")
            QMessageBox.warning(self, "No camera", "No working camera detected.")
            return
        
        print(f"[UI] ✓ Camera found at index {cam_idx}")

        self.cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("[UI] ✗ Failed to open camera")
            QMessageBox.warning(self, "Camera open failed", "Could not open camera.")
            return

        print("[UI] ✓ Camera opened successfully")

        self.session_manager.start_session()
        self.analytics = SessionAnalytics()
        self.session_events = []

        self.timer.start(16)
        print("[UI] ✓ Frame timer started (60 FPS)")
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.info_label.setText("Session started... Point camera at face for emotion detection")

    def stop_session(self):
        self._end_session(finalize_playlist=True, show_summary=True)

    def _end_session(self, finalize_playlist: bool, show_summary: bool) -> None:
        self.timer.stop()

        if self.cap:
            self.cap.release()
            self.cap = None

        self.session_manager.end_session()

        if finalize_playlist:
            played_songs = self.rolling_player.spotify.song_queue.get_played_songs()
            if len(played_songs) >= 10:
                playlist_id = self.rolling_player.finalize_session()
                if show_summary:
                    self._save_session_summary(self.session_events, playlist_id)
            else:
                print("[UI] Fewer than 10 songs were played this session; skipping playlist creation.")
                if show_summary:
                    QMessageBox.information(
                        self,
                        "Session Summary",
                        "Fewer than 10 songs were played, so no Spotify playlist was created."
                    )

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.info_label.setText("Session stopped. Check Spotify for your emotion mix playlist!")

    # -------------------------
    # Frame Loop
    # -------------------------
    def _update_frame(self):
        if self.cap is None:
            return

        try:
            ret, frame = self.cap.read()
            if not ret:
                print("[UI] Camera read failed")
                return

            # FPS calculation
            now = time.time()
            dt = now - self.last_ts if self.last_ts else 0.001
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
            self.last_ts = now

            # Gesture detection
            gesture_label, gesture_conf = self.gesture_detector.detect_gesture(frame)
            if gesture_label in {"Rock", "ThumbsUp", "ThumbsDown"}:
                detected_emotion = {
                    "Rock": "Rock",
                    "ThumbsUp": "Happy",
                    "ThumbsDown": "Sad",
                }[gesture_label]
                conf = gesture_conf
                annotated = frame.copy()
                cv2.putText(
                    annotated,
                    f"{gesture_label} ({gesture_conf:.2f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 200, 0),
                    2,
                )
            else:
                # Emotion detection
                if hasattr(self.detector, "predict_frame"):
                    label, conf, annotated = self.detector.predict_frame(frame)
                else:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    label, conf = self.detector.predict(gray)
                    annotated = frame.copy()
                    if label:
                        cv2.putText(
                            annotated,
                            f"{label} ({conf:.2f})",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 200, 0),
                            2,
                        )

                # Confidence gating
                if not label or conf < CONFIDENCE_THRESHOLD:
                    detected_emotion = "Neutral"
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
            
        except Exception as e:
            print(f"[UI] Frame error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

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
        self.is_shutting_down = True
        self._end_session(finalize_playlist=False, show_summary=False)
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
