import os
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
import cv2
import numpy as np
from pathlib import Path

# Load environment vars
load_dotenv(dotenv_path = "../../.env")

# Configuration for capture card
CAPTURE_CARD_INDEX = int(os.getenv("CAPTURE_CARD_INDEX", "0"))  # Default to device 0

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

# Initialize the FastAPI app
app = FastAPI(
    title="Screen Analysis API",
    description="An API that analyzes a screenshot based on an audio command."
)

try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

@app.post("/analyze-screen/",
          summary="Analyze Screen with Audio Command",
          description="Takes an audio file and a screenshot, analyzes the image based on the audio, and returns an audio response.",
          tags=["Analysis"])
async def analyze_screen(audio_file: UploadFile = File(..., description="Audio command file (e.g., mp3, wav).")):
    """
    This endpoint processes an audio command to analyze a real-time screenshot.
    """
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized. Check API key.")
    
    try:
        print("Transcribing audio...")
        audio_bytes = await audio_file.read()
        file_tuple = (
            audio_file.filename or "audio.wav",
            audio_bytes,
            audio_file.content_type or "audio/wav",
        )

        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=file_tuple,
        )
        user_prompt = transcription.text
        print(f"User prompt: '{user_prompt}'")
        print("Taking screenshot from capture card...")

        try:
            frame = capture_from_capture_card()
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            success, png_bytes = cv2.imencode('.png', frame_rgb)
            if not success:
                raise Exception("Failed to encode frame as PNG")
            base64_image = base64.b64encode(png_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"Capture card error: {e}")
            available_devices = list_video_devices()
            print(f"Available video devices: {available_devices}")
            raise HTTPException(status_code=500, detail=f"Capture card error: {e}")

        print("Analyzing screenshot with GPT-4o...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": "You are a gaming assistant that tells the user what's on the screen. Your answers should be as few words as possible."
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

        print("Generating audio response...")
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=analysis_text
        )

        # stream the audio in chunks
        return StreamingResponse(speech_response.iter_bytes(), media_type="audio/mpeg")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Server is running. Nothing to see here."}

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