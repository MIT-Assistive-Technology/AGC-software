from screenshot_encoded import capture, encode_image_base64, save_screenshot

def test_ai_ready_capture():
    # Try capture card first
    try:
        img = capture(source="capture_card", camera_index=1)
        print("🎥 Captured frame from capture card.")
    except Exception as e:
        print(f"⚠️ {e}. Falling back to PC screenshot.")
        img = capture(source="pc")

    # Convert to base64 for AI
    encoded = encode_image_base64(img)
    print(f"✅ Encoded image length: {len(encoded)} characters")

    # Optionally save a copy for your logs
    path = save_screenshot(img)
    print(f"🖼️ Saved screenshot: {path}")

if __name__ == "__main__":
    test_ai_ready_capture()
