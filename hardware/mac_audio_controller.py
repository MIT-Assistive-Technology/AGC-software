#!/usr/bin/env python3
"""
macOS Audio Controller Script (Python 3.9+ Compatible)

This script runs on macOS and interacts with the screen analysis server:
1. Waits for the spacebar to be pressed.
2. Records audio from the microphone.
3. Sends the audio to the server's /analyze-screen/ endpoint.
4. Receives an audio response and plays it back.
"""

import os
import sys
import time
import requests
import logging
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as write_wav
from pynput import keyboard
from threading import Event
from typing import Optional 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Change this to the IP address of the computer running the FastAPI server
SERVER_HOST = "127.0.0.1" # Use 127.0.0.1 if server is on the same Mac
SERVER_PORT = 8000
AUDIO_SAMPLE_RATE = 44100
RECORDING_DURATION = 4  # seconds

os.makedirs("temp", exist_ok=True) # this is where the audio files will be saved
TEMP_RECORDING_PATH = "temp/temp_recording.wav"
TEMP_RESPONSE_PATH = "temp/temp_response.mp3"

class MacOSAudioController:
    """Controller class for macOS audio operations, triggered by the spacebar."""
    
    def __init__(self, server_host: str = SERVER_HOST, server_port: int = SERVER_PORT):
        self.server_url = f"http://{server_host}:{server_port}"
        self.processing = False
        self.spacebar_pressed = Event() # A thread-safe event flag

    def start_keyboard_listener(self):
        """Starts a non-blocking keyboard listener."""
        listener = keyboard.Listener(on_press=self.on_key_press)
        listener.daemon = True
        listener.start()
        logger.info("Keyboard listener started. Press the spacebar to trigger recording.")

    def on_key_press(self, key):
        """Callback function for keyboard press events."""
        if key == keyboard.Key.space:
            if not self.processing:
                logger.info("Spacebar pressed!")
                self.spacebar_pressed.set()
            else:
                logger.info("Spacebar pressed, but currently processing. Please wait.")
    
    def record_audio(self, duration: int = RECORDING_DURATION) -> Optional[str]:
        """
        Record audio from the default microphone and save it as a WAV file.
        """
        try:
            logger.info(f"Recording for {duration} seconds...")
            recording = sd.rec(
                int(duration * AUDIO_SAMPLE_RATE),
                samplerate=AUDIO_SAMPLE_RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()

            write_wav(TEMP_RECORDING_PATH, AUDIO_SAMPLE_RATE, recording)
            logger.info(f"Audio recorded and saved to {TEMP_RECORDING_PATH}")
            return TEMP_RECORDING_PATH
        except Exception as e:
            logger.error(f"Audio recording failed: {e}")
            return None
    
    def send_audio_to_server(self, audio_file_path: str) -> Optional[str]:
        """
        Send an audio file to the server and save the returned audio response.
        """
        try:
            url = f"{self.server_url}/analyze-screen/"
            logger.info(f"Sending audio to server: {url}")

            with open(audio_file_path, 'rb') as audio_file:
                files = {'audio_file': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
                
                response = requests.post(url, files=files, timeout=30, stream=True)
                
                if response.status_code == 200:
                    logger.info("Successfully received audio response from server.")
                    with open(TEMP_RESPONSE_PATH, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=1024):
                            f.write(chunk)
                    logger.info(f"Response saved to {TEMP_RESPONSE_PATH}")
                    return TEMP_RESPONSE_PATH
                else:
                    logger.error(f"Server error: {response.status_code} - {response.text}")
                    return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with server: {e}")
            return None
    
    def play_audio_response(self, response_audio_path: str) -> bool:
        """
        Play the audio file received from the server using macOS's 'afplay'.
        """
        if not os.path.exists(response_audio_path):
            logger.error("Response audio file not found.")
            return False
        try:
            logger.info(f"Playing response: {response_audio_path}")
            os.system(f"afplay {response_audio_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to play audio response: {e}")
            return False
    
    def check_server_health(self) -> bool:
        """Check if the server is reachable."""
        try:
            response = requests.get(f"{self.server_url}/", timeout=5) # this is the root endpoint we defined 
            return response.status_code == 200
        except requests.exceptions.RequestException:
            logger.error(f"Server at {self.server_url} is not reachable.")
            return False
    
    def cleanup(self):
        """Clean up temporary audio files."""
        for path in [TEMP_RECORDING_PATH, TEMP_RESPONSE_PATH]:
            if os.path.exists(path):
                os.remove(path)

    def run_voice_command_cycle(self):
        """Run a complete voice command cycle: record -> send -> play response."""
        self.processing = True
        
        try:
            if not self.check_server_health():
                return
            
            recorded_file = self.record_audio()
            if not recorded_file:
                return

            response_file = self.send_audio_to_server(recorded_file)
            if not response_file:
                return

            self.play_audio_response(response_file)
            
        finally:
            self.processing = False
            self.cleanup()
            logger.info("\nCycle finished. Press the spacebar for the next command.")
    
    def run_continuous_mode(self):
        """Run the controller in continuous mode, waiting for spacebar presses."""
        self.start_keyboard_listener()
        try:
            while True:
                self.spacebar_pressed.wait()
                self.run_voice_command_cycle()
                self.spacebar_pressed.clear()

        except KeyboardInterrupt:
            logger.info("\nExiting program.")
            self.cleanup()
            sys.exit(0)

def main():
    controller = MacOSAudioController(server_host=SERVER_HOST)
    controller.run_continuous_mode()

if __name__ == "__main__":
    main()