import os
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
import mss
import mss.tools
from pathlib import Path

# Load environment vars
load_dotenv(dotenv_path = "../../.env")

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
        print("Taking screenshot...")
        with mss.mss() as sct:
            # screenshot the primary monitor
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)

            # raw BGRA image to PNG bytes and encode to base64
            png_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
            base64_image = base64.b64encode(png_bytes).decode('utf-8')

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