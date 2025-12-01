import os
import base64
import struct
import wave
from io import BytesIO
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import Response
from openai import OpenAI
from dotenv import load_dotenv
import cv2
import numpy as np
from PIL import ImageGrab, Image
import platform
import time
import io

# Load environment vars
load_dotenv(dotenv_path="../../.env")

# Configuration for capture card
CAPTURE_CARD_INDEX = int(os.getenv("CAPTURE_CARD_INDEX", "0"))

def list_video_devices():
    """List all available video capture devices."""
    devices = []
    index = 0
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            devices.append(index)
        cap.release()
        index += 1
    return devices

def capture_from_capture_card(device_index: int = CAPTURE_CARD_INDEX):
    """
    Capture a frame from the specified capture card device.
    Returns the frame as a numpy array, or None if capture fails.
    """
    cap = cv2.VideoCapture(device_index)
    
    if not cap.isOpened():
        raise Exception(f"Could not open video device {device_index}")
    
    try:
        ret, frame = cap.read()
        if not ret:
            raise Exception(f"Could not read frame from video device {device_index}")
        return frame
    finally:
        cap.release()

def capture_screen_screenshot():
    """
    Capture a screenshot of the entire screen using PIL.
    Returns the frame as a numpy array.
    """
    try:
        # Capture the entire screen
        screenshot = ImageGrab.grab()
        
        # Convert PIL Image to numpy array (RGB)
        frame_rgb = np.array(screenshot)
        
        # Convert RGB to BGR for consistency with OpenCV
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        return frame_bgr
    except Exception as e:
        raise Exception(f"Failed to capture screenshot: {e}")

def pcm_to_wav(pcm_data: bytes, sample_rate: int, bits_per_sample: int, channels: int) -> bytes:
    """
    Convert raw PCM data to WAV format for Whisper API using wave module.
    """
    wav_io = BytesIO()
    
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(bits_per_sample // 8)  # 16 bits = 2 bytes
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    
    return wav_io.getvalue()

def resample_audio(audio_data: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
    """
    Resample audio data from original sample rate to target sample rate.
    Uses linear interpolation.
    """
    if orig_rate == target_rate:
        return audio_data
    
    # Calculate the new length
    duration = len(audio_data) / orig_rate
    target_length = int(duration * target_rate)
    
    # Create indices for interpolation
    orig_indices = np.linspace(0, len(audio_data) - 1, len(audio_data))
    target_indices = np.linspace(0, len(audio_data) - 1, target_length)
    
    # Interpolate
    resampled = np.interp(target_indices, orig_indices, audio_data)
    
    return resampled.astype(audio_data.dtype)

def mp3_to_pcm(mp3_data: bytes, target_sample_rate: int = 16000) -> bytes:
    """
    Convert MP3 data to raw PCM format for the Pico.
    Returns 16-bit signed PCM audio at the target sample rate.
    
    Note: OpenAI TTS returns MP3. We decode it and convert to PCM.
    This uses a simple approach without external dependencies.
    """
    # Since we can't easily decode MP3 without ffmpeg/pydub,
    # we'll request WAV format from OpenAI instead.
    # This function is kept for compatibility but won't be used.
    raise NotImplementedError("MP3 decoding requires ffmpeg. Use WAV format instead.")

# Initialize the FastAPI app
app = FastAPI(
    title="Screen Analysis API",
    description="An API that analyzes a screenshot based on an audio command from Pico."
)

API_KEY = "insert API key"
try:
    client = OpenAI(api_key=API_KEY)
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

@app.post("/analyze-screen/",
          summary="Analyze Screen with Audio Command from Pico",
          description="Takes raw PCM audio from Pico, analyzes the image, and returns PCM audio response.",
          tags=["Analysis"])
async def analyze_screen(
    request: Request,
    use_capture_card: bool = Query(
        False,
        description="If True, use capture card. If False, use screen screenshot."
    )
):
    """
    This endpoint processes raw PCM audio from the Pico to analyze a real-time screenshot.
    
    Query Parameters:
        use_capture_card (bool): Set to True to use capture card, False for screen screenshot
    """
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized. Check API key.")
    
    try:
        time0 = time.time()
        # Get audio metadata from headers
        sample_rate = int(request.headers.get('X-Sample-Rate', 16000))
        bits_per_sample = int(request.headers.get('X-Bits-Per-Sample', 16))
        channels = int(request.headers.get('X-Channels', 1))
        
        print(f"\n{'='*50}")
        print("Received audio from Pico:")
        print(f"  Sample Rate: {sample_rate} Hz")
        print(f"  Bits: {bits_per_sample}")
        print(f"  Channels: {channels}")
        
        # Read raw PCM audio data
        pcm_data = await request.body()
        print(f"  Size: {len(pcm_data)} bytes")
        print(f"  Duration: {len(pcm_data) / (sample_rate * channels * (bits_per_sample // 8)):.2f}s")
        
        # Convert PCM to WAV for Whisper
        print("\nConverting PCM to WAV...")
        wav_data = pcm_to_wav(pcm_data, sample_rate, bits_per_sample, channels)
        
        # Transcribe audio
        print("Transcribing audio with Whisper...")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", wav_data, "audio/wav"),
        )
        user_prompt = transcription.text
        print(f"User prompt: '{user_prompt}'")
        
        # Capture image based on mode
        print(f"\nCapturing image (mode: {'capture card' if use_capture_card else 'screen screenshot'})...")
        try:
            if use_capture_card:
                # Use capture card
                frame = capture_from_capture_card()
                print(f"  ✅ Captured from capture card (device {CAPTURE_CARD_INDEX})")
            else:
                # Use screen screenshot
                frame = capture_screen_screenshot()
                print(f"  ✅ Captured screen screenshot")
            
            # Convert to RGB and encode as PNG
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            success, png_bytes = cv2.imencode('.png', frame_rgb)
            if not success:
                raise Exception("Failed to encode frame as PNG")
            
            # convert to jpeg and reduce image size
            buf = io.BytesIO()
            img = Image.open(io.BytesIO(png_bytes))
            img.save(buf, format="JPEG", quality=70)  # quality 0-100
            jpeg_bytes = buf.getvalue()
            base64_image = base64.b64encode(jpeg_bytes).decode('utf-8')

            #base64_image = base64.b64encode(png_bytes).decode('utf-8')
            print("Image size: " + str(len(base64_image)))
            print(f"  Image size: {frame.shape[1]}x{frame.shape[0]}")
            
        except Exception as e:
            if use_capture_card:
                print(f"Capture card error: {e}")
                available_devices = list_video_devices()
                print(f"Available video devices: {available_devices}")
                raise HTTPException(status_code=500, detail=f"Capture card error: {e}")
            else:
                print(f"Screenshot error: {e}")
                raise HTTPException(status_code=500, detail=f"Screenshot error: {e}")
        time1 = time.time()
        print("After receiving, before sending to OpenAI: " + str((time1-time0)))
        # Analyze with GPT-4o
        print("\nAnalyzing image with GPT-4.1 Nano...")
        response = client.chat.completions.create(
            model="gpt-4.1-nano", #gpt-4.1-nano
            messages=[
                {
                    "role": "system",
                    "content": "You are a gaming assistant that tells the user what's on the screen. Your answers should be shorter than 5 words."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low" 
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        analysis_text = response.choices[0].message.content
        print(f"Analysis result: '{analysis_text}'")
        time2 = time.time()
        print("OpenAI text send+processing+receive time: " + str((time2-time1)))

        # Generate TTS audio
        print("\nGenerating audio response...")
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=analysis_text,
            response_format="pcm"  # Request PCM directly instead of MP3
        )
        time3 = time.time()
        print("OpenAI voice send+processing+receive time: " + str((time3-time2)))
        # Get PCM data directly from OpenAI
        pcm_data = speech_response.content
        print(f"Generated PCM: {len(pcm_data)} bytes")
        
        # OpenAI returns PCM at 24kHz, 16-bit, mono by default
        # We need to resample to match the Pico's sample rate
        openai_sample_rate = 24000
        
        if openai_sample_rate != sample_rate:
            print(f"Resampling from {openai_sample_rate}Hz to {sample_rate}Hz...")
            # Convert bytes to numpy array
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
            # Resample
            resampled_array = resample_audio(audio_array, openai_sample_rate, sample_rate)
            # Convert back to bytes
            pcm_response = resampled_array.astype(np.int16).tobytes()
        else:
            pcm_response = pcm_data
        
        print(f"PCM output: {len(pcm_response)} bytes")
        print(f"Duration: {len(pcm_response) / (sample_rate * 2):.2f}s")
        print(f"{'='*50}\n")
        
        # Return raw PCM data
        time4 = time.time()
        print("Between getting OpenAI sound and sending: " + str((time4-time3)))
        print("Total server time = " + str(time4-time0))

        return Response(
            content=pcm_response,
            media_type="application/octet-stream",
            headers={
                'X-Sample-Rate': str(sample_rate),
                'X-Bits-Per-Sample': '16',
                'X-Channels': '1'
            }
        )

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Server is running. Ready for Pico audio requests.",
        "platform": platform.system(),
        "endpoints": {
            "analyze_screen": "/analyze-screen/?use_capture_card=false (or true)",
            "video_devices": "/video-devices"
        }
    }

@app.get("/video-devices", 
         summary="List Available Video Devices",
         description="Returns a list of available video capture devices.",
         tags=["Debug"])
async def get_video_devices():
    """Endpoint to list all available video capture devices."""
    try:
        devices = list_video_devices()
        return {
            "available_devices": devices,
            "current_capture_card_index": CAPTURE_CARD_INDEX,
            "message": f"Found {len(devices)} video device(s). Current capture card is set to device {CAPTURE_CARD_INDEX}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test-screenshot",
         summary="Test Screenshot Capture",
         description="Test both capture methods and return info about them.",
         tags=["Debug"])
async def test_screenshot():
    """Test endpoint to verify both screenshot methods work."""
    results = {
        "screen_screenshot": None,
        "capture_card": None
    }
    
    # Test screen screenshot
    try:
        frame = capture_screen_screenshot()
        results["screen_screenshot"] = {
            "status": "success",
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
            "channels": frame.shape[2] if len(frame.shape) > 2 else 1
        }
    except Exception as e:
        results["screen_screenshot"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Test capture card
    try:
        frame = capture_from_capture_card()
        results["capture_card"] = {
            "status": "success",
            "device_index": CAPTURE_CARD_INDEX,
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
            "channels": frame.shape[2] if len(frame.shape) > 2 else 1
        }
    except Exception as e:
        results["capture_card"] = {
            "status": "error",
            "error": str(e),
            "device_index": CAPTURE_CARD_INDEX
        }
    
    return results
# ipconfig getifaddr en0
# To run: uvicorn main:app --reload --host hostIP --port 8000