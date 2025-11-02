import machine
import time
import array
import network
import urequests
import struct
from machine import I2S, Pin

# --- CONFIGURATION ---
# Update these with your network details
WIFI_SSID = "MIT"
WIFI_PASSWORD = "$$4b4P(LwG"

# Update with your computer's IP address (find using ipconfig/ifconfig)
# ipconfig getifaddr en0
# Make sure to use port 8000
SERVER_IP = "10.29.151.42"
SERVER_PORT = "8000"

# Choose capture mode:
# False = Screen screenshot (captures entire screen on server)
# True = Capture card (captures from video capture device)
USE_CAPTURE_CARD = False

# --- Pin Definitions ---
# Microphone (SPH0645LM4H) - I2S 0
MIC_BCLK_PIN = 9
MIC_WS_PIN = 10
MIC_SD_PIN = 11

# Amplifier (MAX98357) - I2S 1
AMP_BCLK_PIN = 12
AMP_WS_PIN = 13
AMP_SD_PIN = 14

# Button
BUTTON_PIN_NUM = 15  # GP15

# --- Audio Configuration ---
SAMPLE_RATE = 16000
BITS_PER_SAMPLE = 16
RECORD_SECONDS = 3  # Record for 3 seconds
NUM_SAMPLES = SAMPLE_RATE * RECORD_SECONDS

print("=" * 50)
print("Gaming Assistant - Audio Control")
print("=" * 50)
print(f"Capture Mode: {'Capture Card' if USE_CAPTURE_CARD else 'Screen Screenshot'}")
print()

def connect_wifi():
    """Connect to WiFi network."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        print("✅ Already connected to WiFi")
        print(f"   IP: {wlan.ifconfig()[0]}")
        return wlan
    
    print(f"📡 Connecting to: {WIFI_SSID}")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print("   Waiting for connection...")
        time.sleep(1)
    
    if wlan.isconnected():
        print("✅ WiFi connected!")
        print(f"   IP: {wlan.ifconfig()[0]}")
        return wlan
    else:
        print("❌ WiFi connection failed!")
        return None

# Connect to WiFi
wlan = connect_wifi()
if not wlan:
    print("Cannot proceed without WiFi. Exiting.")
    raise SystemExit

print()

# --- Initialize Microphone ---
try:
    i2s_mic = I2S(
        0,
        sck=Pin(MIC_BCLK_PIN),
        ws=Pin(MIC_WS_PIN),
        sd=Pin(MIC_SD_PIN),
        mode=I2S.RX,
        bits=BITS_PER_SAMPLE,
        format=I2S.MONO,
        rate=SAMPLE_RATE,
        ibuf=4096
    )
    print("✅ Microphone initialized")
except Exception as e:
    print(f"❌ Failed to initialize microphone: {e}")
    raise SystemExit

# --- Initialize Amplifier ---
try:
    i2s_amp = I2S(
        1,
        sck=Pin(AMP_BCLK_PIN),
        ws=Pin(AMP_WS_PIN),
        sd=Pin(AMP_SD_PIN),
        mode=I2S.TX,
        bits=BITS_PER_SAMPLE,
        format=I2S.MONO,
        rate=SAMPLE_RATE,
        ibuf=4096
    )
    print("✅ Amplifier initialized")
except Exception as e:
    print(f"❌ Failed to initialize amplifier: {e}")
    i2s_mic.deinit()
    raise SystemExit

# --- Initialize Button ---
button = Pin(BUTTON_PIN_NUM, Pin.IN, Pin.PULL_UP)

print()

# Create audio buffer
audio_buffer = array.array('h', (0 for _ in range(NUM_SAMPLES)))

print("=" * 50)
print("🎮 Ready! Press the button to ask about the game.")
print("=" * 50)
print()
try:
    while True:
        # Wait for button press
        # button.value() is 1 (HIGH) when not pressed (PULL_UP)
        # and 0 (LOW) when pressed
        while button.value() == 1:
            time.sleep(0.01)
        
        # Debounce
        time.sleep(0.05)
        
        # Confirm button is still pressed
        if button.value() == 0:
            print("\n🎤 RECORDING...")
            print(f"   Speak your question ({RECORD_SECONDS} seconds)")
            
            # Record audio
            start_time = time.ticks_ms()
            bytes_read = i2s_mic.readinto(audio_buffer)
            record_time = time.ticks_diff(time.ticks_ms(), start_time) / 1000.0
            
            print(f"✅ Recording complete ({record_time:.2f}s)")
            print(f"   Bytes recorded: {bytes_read}")
            
            # Check audio levels
            min_val = min(audio_buffer)
            max_val = max(audio_buffer)
            spread = max_val - min_val
            print(f"   Audio level: {spread}")
            
            if spread < 100:
                print("   ⚠️  Very quiet - speak louder!")
            
            # Send to server
            print("\n📤 Sending to server...")
            
            # Build URL with query parameter
            server_url = f"http://{SERVER_IP}:{SERVER_PORT}/analyze-screen/?use_capture_card={'true' if USE_CAPTURE_CARD else 'false'}"
            print(f"   URL: {server_url}")
            print(f"   Mode: {'Capture Card' if USE_CAPTURE_CARD else 'Screen Screenshot'}")
            
            # Use memoryview to access array buffer directly without copying
            # This is much more memory efficient
            try:
                # Try to get raw bytes directly from buffer
                audio_bytes = bytes(memoryview(audio_buffer))
            except:
                # Fallback: convert in smaller chunks if memoryview doesn't work
                print("   Converting audio in chunks...")
                chunk_size = 512
                chunks = []
                for i in range(0, len(audio_buffer), chunk_size):
                    chunk = audio_buffer[i:i+chunk_size]
                    chunk_bytes = struct.pack(f'{len(chunk)}h', *chunk)
                    chunks.append(chunk_bytes)
                audio_bytes = b''.join(chunks)
            
            headers = {
                'Content-Type': 'application/octet-stream',
                'X-Sample-Rate': str(SAMPLE_RATE),
                'X-Bits-Per-Sample': str(BITS_PER_SAMPLE),
                'X-Channels': '1'
            }
            
            try:
                response = urequests.post(
                    server_url,
                    data=audio_bytes,
                    headers=headers,
                    timeout=30  # Longer timeout for processing
                )
                
                if response.status_code == 200:
                    print(f"✅ Response received!")
                    print(f"   Size: {len(response.content)} bytes")
                    
                    # Convert response to audio array
                    received_audio = array.array('h')
                    
                    for i in range(0, len(response.content), 2):
                        if i + 1 < len(response.content):
                            sample = int.from_bytes(
                                response.content[i:i+2],
                                'little',
                                True
                            )
                            received_audio.append(sample)
                    
                    duration = len(received_audio) / SAMPLE_RATE
                    print(f"   Duration: {duration:.2f}s")
                    
                    # Play response
                    print("\n🔊 Playing response...")
                    
                    if len(received_audio) > 0:
                        i2s_amp.write(received_audio)
                        print("✅ Playback complete!")
                    else:
                        print("❌ No audio data received")
                
                else:
                    print(f"❌ Server error: {response.status_code}")
                    if len(response.text) > 0:
                        print(f"   {response.text[:200]}")
                
                response.close()
                
            except Exception as e:
                print(f"❌ Communication error: {e}")
            
            # Wait for button release
            while button.value() == 0:
                time.sleep(0.01)
            
            print("\n" + "=" * 50)
            print("Ready for next question. Press button to ask.")
            print("=" * 50)

except KeyboardInterrupt:
    print("\n\n⚠️  Interrupted by user")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import sys
    sys.print_exception(e)
    
finally:
    # Clean up
    i2s_mic.deinit()
    i2s_amp.deinit()
    print("\nI2S devices deinitialized")
    print("Goodbye!")
