"""
screenshot_encoder.py
Cross-platform screenshot + base64 encoder.
Supports:
 - macOS and Windows screen captures
 - Capture cards (treated as camera devices via OpenCV)
"""

import platform
import pyautogui
import cv2
from PIL import Image
from datetime import datetime
from pathlib import Path
import base64
import io

def detect_source(preferred_source=None, camera_index=0):
    """
    Automatically detect whether to use screen capture or capture card.
    - preferred_source: "pc" or "capture_card" (optional)
    """
    if preferred_source:
        return preferred_source

    cap = cv2.VideoCapture(camera_index)
    if cap.isOpened():
        cap.release()
        return "capture_card"
    return "pc"


def capture(source=None, region=None, camera_index=0):
    """
    Capture an image from screen or capture card feed.
    Returns a Pillow Image.
    """
    system = platform.system().lower()
    active_source = detect_source(source, camera_index)

    if active_source == "pc":
        print(f"🖥️ Capturing {system} screen...")
        return pyautogui.screenshot(region=region)

    elif active_source == "capture_card":
        print(f"🎮 Capturing frame from capture card (index {camera_index})...")
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError("❌ Could not open capture card.")

        # Warm-up for a few frames
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise RuntimeError("❌ Failed to capture frame from capture card.")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
    else:
        raise ValueError("Invalid source specified.")


def encode_image_base64(image):
    """Convert a Pillow Image into a base64-encoded PNG string."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def save_image(image, output_dir="screenshots"):
    """Save the image locally."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/screenshot_{timestamp}.png"
    image.save(path)
    return path


def save_base64(encoded_str, output_dir="screenshots"):
    """Save the base64 string to a text file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{output_dir}/encoded_{timestamp}.txt"
    with open(path, "w") as f:
        f.write(encoded_str)
    return path
