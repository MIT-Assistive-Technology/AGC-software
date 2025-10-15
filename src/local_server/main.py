import os
import base64
from io import BytesIO
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
import mss
import mss.tools

# Load environment variables from .env file (for the API key)
load_dotenv()

# Initialize the FastAPI app
app = FastAPI(
    title="Screen Analysis API",
    description="An API that analyzes a screenshot based on an audio command."
)

# Initialize the OpenAI client
# The client automatically looks for the OPENAI_API_KEY in environment variables
try:
    client = OpenAI()
except Exception as e:
    # This will catch the error if the API key is not set
    print(f"Error initializing OpenAI client: {e}")
    print("Please make sure your OPENAI_API_KEY is set in the .env file.")
    client = None

@app.post("/analyze-screen/",
          summary="Analyze Screen with Audio Command",
          description="Takes an audio file and a screenshot, analyzes the image based on the audio, and returns an audio response.",
          tags=["Analysis"])
async def analyze_screen(audio_file: UploadFile = File(..., description="Audio command file (e.g., mp3, wav).")):
    """
    This endpoint processes an audio command to analyze a real-time screenshot.

    - **Receives**: An audio file.
    - **Transcribes**: The audio to text using Whisper.
    - **Captures**: A screenshot of the primary display.
    - **Analyzes**: The screenshot using GPT-4o with the transcribed text as a prompt.
    - **Responds**: With a generated audio file (TTS) containing the analysis.
    """
    if not client:
        raise HTTPException(status_code=500, detail="OpenAI client not initialized. Check API key.")

    try:
        # --- Step 1: Transcribe the user's audio command ---
        print("Transcribing audio...")
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file.file
        )
        user_prompt = transcription.text
        print(f"User prompt: '{user_prompt}'")

        # --- Step 2: Take a screenshot ---
        print("Taking screenshot...")
        with mss.mss() as sct:
            # Grab the data of the primary monitor
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)

            # Convert the raw BGRA image to a PNG in memory
            img_bytes_io = BytesIO()
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=img_bytes_io)
            img_bytes_io.seek(0)
            
            # Encode the PNG image to a base64 string
            base64_image = base64.b64encode(img_bytes_io.read()).decode('utf-8')

        # --- Step 3: Analyze the screenshot with GPT-4o ---
        print("Analyzing screenshot with GPT-4o...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "low" # Use 'low' for faster processing
                            },
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        analysis_text = response.choices[0].message.content
        print(f"Analysis result: '{analysis_text}'")

        # --- Step 4: Convert the analysis text back to audio ---
        print("Generating audio response...")
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=analysis_text
        )

        # --- Step 5: Stream the audio back to the client ---
        # StreamingResponse is efficient as it sends the audio in chunks
        return StreamingResponse(speech_response.iter_bytes(), media_type="audio/mpeg")

    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Server is running. Go to /docs for API documentation."}