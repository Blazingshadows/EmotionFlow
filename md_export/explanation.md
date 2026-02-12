# System Explanation

## Overview

This Emotion Driven Music Recommendation System combines computer vision, deep learning, and music streaming to create a personalized listening experience based on the user's emotional state.

## How It Works

### 1. Emotion Detection
- Captures video feed from the user's webcam
- Detects faces using YOLO-based face detection
- Classifies emotions using trained neural networks (MiniXception or MobileNetV2)
- Recognizes 7 emotions: angry, disgust, fear, happy, neutral, sad, surprise

### 2. Music Recommendation
- Maps detected emotions to music characteristics (tempo, valence, energy)
- Queries music database or Spotify API for matching tracks
- Maintains a rolling playlist that adapts to emotional changes
- Smooths recommendations to avoid jarring transitions

### 3. Session Management
- Tracks user emotions over time
- Stores session history and analytics
- Provides insights into emotional patterns
- Enables playback of previous sessions

### 4. User Interface
- Clean, intuitive interface for interaction
- Real-time emotion display
- Music player controls
- Session analytics visualization

## Technical Stack

- **Deep Learning**: PyTorch for emotion classification
- **Computer Vision**: OpenCV for face detection and video processing
- **Music API**: Spotify Web API for music streaming
- **UI Framework**: Custom UI components

## Models Used

### MiniXception
- Lightweight CNN architecture
- Trained on FER2013 dataset
- Optimized for real-time inference

### MobileNetV2
- Efficient architecture for mobile/edge deployment
- Fine-tuned on AffectNet dataset
- Higher accuracy with reasonable performance
