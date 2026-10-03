# Hand Gesture Camera & Desktop Controller

<div align="center">
  <img src="https://img.shields.io/badge/AI_Vision-MediaPipe-00897B?style=for-the-badge&logo=google&logoColor=white" alt="MediaPipe" />
  <img src="https://img.shields.io/badge/Computer_Vision-OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV" />
  <img src="https://img.shields.io/badge/Language-Python_3.x-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</div>

<br />

An advanced computer vision system enabling **touchless hand gesture control** for camera streams, desktop navigation, and remote mobile interaction. Powered by **Google MediaPipe Hand Landmarker** and **OpenCV**.

---

## Key Capabilities

- **Real-Time 21-Landmark Hand Tracking:** High precision 3D hand landmark coordinate estimation.
- **Desktop Control Mode (desktop_controller.py):** Control media, volume, navigation, or mouse movement touchlessly via gesture signals.
- **Mobile Web Stream Mode (mobile_controller.py):** Stream camera feeds and trigger actions through a lightweight web interface.
- **Low Latency Inference:** Optimized for smooth real-time FPS on consumer webcams without dedicated GPUs.

---

## Tech Stack

- **Vision Pipeline:** Google MediaPipe (hand_landmarker.task), OpenCV (cv2)
- **Backend / Stream:** Python 3.x, Flask
- **Frontend Controller:** HTML5, CSS3, JavaScript

---

## Quickstart Guide

1. **Clone the repository:**
   ```bash
   git clone https://github.com/shrihari12012007-web/Hand_Gesture_Camera..git
   cd Hand_Gesture_Camera.
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Controller:**
   - **For Desktop Gesture Control:**
     ```bash
     python desktop_controller.py
     ```
   - **For Mobile Web Controller:**
     ```bash
     python mobile_controller.py
     ```

---

Developed by Shree Hari S B
