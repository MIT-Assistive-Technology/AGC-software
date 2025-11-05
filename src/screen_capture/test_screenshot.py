from screenshot_encoded import capture, encode_image_base64, save_image, save_base64
"""
test_screenshot_encoder.py
Tests screenshot + base64 encoding on macOS, Windows, and capture card setups.
"""

def test_cross_platform_capture(camera_index=0):
    print("🔍 Starting cross-platform screenshot test...")
    try:
        # Attempt capture card first
        img = capture(source="capture_card", camera_index=camera_index)
        print("✅ Successfully captured frame from capture card.")
    except Exception as e:
        print(f"⚠️ Capture card not available ({e}). Falling back to screen capture.")
        img = capture(source="pc")

    # Encode to base64
    encoded = encode_image_base64(img)
    print(f"✅ Base64 string length: {len(encoded)} characters")
    # print(f"📄 Preview (first 100 chars): {encoded[:100]}...")

    # Save outputs
    img_path = save_image(img)
    txt_path = save_base64(encoded)

    print(f"🖼️ Screenshot saved to: {img_path}")
    print(f"📜 Base64 text saved to: {txt_path}")
    print("🎉 Test completed successfully!")

if __name__ == "__main__":
    test_cross_platform_capture()
