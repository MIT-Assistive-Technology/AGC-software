import pyautogui
from PIL import Image
from datetime import datetime
from pathlib import Path
import cv2
import base64
import io

def capture(source="pc", region=None, camera_index=0):
    """
    Capture image either from PC screen or from capture card (camera-like device).
    Returns a Pillow Image object.
    """
    if source == "pc":
        # Normal screenshot
        return pyautogui.screenshot(region=region)

    elif source == "capture_card":
        # Capture a single frame from HDMI/camera input
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise RuntimeError("Capture card not detected or cannot be opened.")

        # Warm up camera
        for _ in range(5):
            cap.read()

        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise RuntimeError("Failed to read frame from capture card.")

        # Convert OpenCV image (BGR) to RGB Pillow Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)

    else:
        raise ValueError("Invalid source: use 'pc' or 'capture_card'")


def encode_image_base64(image):
    """
    Convert a Pillow Image into a base64-encoded PNG string.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def save_screenshot(image, path=None, output_dir="screenshots"):
    """
    Optional: save image locally for debugging or logs.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if not path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{output_dir}/screenshot_{timestamp}.png"
    image.save(path)
    return path
