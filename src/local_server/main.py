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
from PIL import ImageGrab
import platform
from ..ai_agent.ai_assistant import CONTROLLER_MAP, _build_mapping_instructions, _normalize_controller_output, _should_apply_controller_normalization
from ..hardware.buttons import press_button
# Load environment vars
load_dotenv(dotenv_path="../../.env")

# Configuration for capture card
CAPTURE_CARD_INDEX = int(os.getenv("CAPTURE_CARD_INDEX", "0"))

def list_video_devices():
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

def capture_from_capture_card(device_index: int = CAPTURE_CARD_INDEX) -> np.ndarray:
    """
    Capture a frame from the specified capture card device.
    """
    cap = cv2.VideoCapture(device_index)
    
    if not cap.isOpened():
        raise Exception(f"Could not open video device {device_index}")
    try:
        ret, frame = cap.read()
        if not ret:
            raise Exception(f"Could not read frame from device {device_index}")
        return frame
    finally:
        cap.release()

def capture_screen_screenshot() -> np.ndarray:
    """
    Capture a screenshot of the entire screen using PIL.
    """
    try:
        screenshot = ImageGrab.grab()
        frame_rgb = np.array(screenshot)
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        return frame_bgr
    except Exception as e:
        raise Exception(f"Failed to capture screenshot: {e}")

def pcm_to_wav(pcm_data: bytes, sample_rate: int, bits_per_sample: int, channels: int) -> bytes:
    """
    Convert raw PCM data to WAV format
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
    interpolate audio data from original sample rate to target sample rate.
    """
    if orig_rate == target_rate:
        return audio_data
    
    duration = len(audio_data) / orig_rate
    target_length = int(duration * target_rate)
    
    orig_indices = np.linspace(0, len(audio_data) - 1, len(audio_data))
    target_indices = np.linspace(0, len(audio_data) - 1, target_length)
    
    resampled = np.interp(target_indices, orig_indices, audio_data)
    
    return resampled.astype(audio_data.dtype)

def mp3_to_pcm(mp3_data: bytes, target_sample_rate: int = 16000) -> bytes:
    """
    Maybe implemented with ffmpeg later, it's annoying 
    """
    raise NotImplementedError("MP3 decoding requires ffmpeg. Use WAV format instead.")

app = FastAPI(
    title="Screen Analysis API",
    description="An API that analyzes a screenshot based on an audio command from Pico."
)


client = OpenAI()

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
            else:
                frame = capture_screen_screenshot()
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            success, png_bytes = cv2.imencode('.png', frame_rgb)
            if not success:
                raise Exception("Failed to encode frame as PNG")
            base64_image = base64.b64encode(png_bytes).decode('utf-8')
            print(f"  Image size: {frame.shape[1]}x{frame.shape[0]}")
            
        except Exception as e:
            if use_capture_card: # debug mode for capture card
                print(f"Capture card error: {e}")
                available_devices = list_video_devices()
                print(f"Available video devices: {available_devices}")
                raise HTTPException(status_code=500, detail=f"Capture card error: {e}")
            else:
                print(f"Screenshot error: {e}")
                raise HTTPException(status_code=500, detail=f"Screenshot error: {e}")

        print("\nAnalyzing image with LLM...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant with vision capabilities. You can analyze images and answer questions about them. "
            "IMPORTANT: For numeric answers, provide only the number and necessary units without explanation. Keep all responses extremely short. "
            "When an image of a game UI is provided and the user asks what to press or how to execute an in-game task, respond with ONLY the controller shorthand symbols separated by single spaces, in the exact order to press, with no extra text. "
            + _build_mapping_instructions()
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low"  # changed to low 
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        analysis_text = response.choices[0].message.content
        print(f"Generated result: '{analysis_text}'")

        if _should_apply_controller_normalization(user_prompt): # we press buttons instead of reading a response
            controller_output = _normalize_controller_output(analysis_text)
            try:
                press_button(controller_output)
            except Exception as e:
                print(f"Error pressing buttons: {e}")
                raise HTTPException(status_code=500, detail=f"Error pressing buttons: {e}")
            return Response( # this needs to be fixed 
                content=analysis_text,
                media_type="text/plain",
            )

        # TTS generation
        print("\nGenerating audio response...")
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=analysis_text,
            response_format="pcm"  # we need PCM directly instead of MP3
        )
        
        pcm_data = speech_response.content
        print(f"Generated PCM: {len(pcm_data)} bytes")
        
        openai_sample_rate = 24000

        if openai_sample_rate != sample_rate:
            print(f"Resampling from {openai_sample_rate}Hz to {sample_rate}Hz...")
            audio_array = np.frombuffer(pcm_data, dtype=np.int16)
            resampled_array = resample_audio(audio_array, openai_sample_rate, sample_rate)
            pcm_response = resampled_array.astype(np.int16).tobytes()
        else:
            pcm_response = pcm_data
        
        print(f"PCM output: {len(pcm_response)} bytes")
        print(f"Duration: {len(pcm_response) / (sample_rate * 2):.2f}s")
        
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

# ipconfig getifaddr en0
# To run: uvicorn main:app --reload --host IP --port 8000