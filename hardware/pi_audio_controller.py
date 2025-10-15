#!/usr/bin/env python3
"""
Raspberry Pi Zero W Audio Controller Script (Updated)

This script runs on a Raspberry Pi and interacts with the screen analysis server:
1. Waits for a button press.
2. Records audio from a microphone.
3. Sends the audio to the server's /analyze-screen/ endpoint.
4. Receives an audio response and plays it back.

Hardware Requirements:
- Raspberry Pi
- USB microphone
- A button and LED connected to GPIO pins.
"""

import os
import sys
import time
import requests
import logging
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write as write_wav
from typing import Optional

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Button functionality will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# ❗️ IMPORTANT: Change this to the IP address of the computer running the server
SERVER_HOST = "192.168.1.100"  
SERVER_PORT = 8000
AUDIO_SAMPLE_RATE = 44100
RECORDING_DURATION = 4  # seconds
TEMP_RECORDING_PATH = "temp_recording.wav"
TEMP_RESPONSE_PATH = "temp_response.mp3"

# GPIO Configuration
BUTTON_PIN = 18  # GPIO pin for the push button
LED_PIN = 24     # GPIO pin for status LED
BUTTON_DEBOUNCE_TIME = 300  # milliseconds


class PiAudioController:
    """Main controller class for Raspberry Pi audio operations."""
    
    def __init__(self, server_host: str = SERVER_HOST, server_port: int = SERVER_PORT):
        self.server_url = f"http://{server_host}:{server_port}"
        self.button_pressed = False
        self.processing = False
        
        if GPIO_AVAILABLE:
            self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for button and LED."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(LED_PIN, GPIO.OUT)
            GPIO.output(LED_PIN, GPIO.LOW)
            GPIO.add_event_detect(
                BUTTON_PIN, 
                GPIO.FALLING, 
                callback=self.button_callback,
                bouncetime=BUTTON_DEBOUNCE_TIME
            )
            logger.info(f"GPIO setup complete - Button: GPIO{BUTTON_PIN}, LED: GPIO{LED_PIN}")
        except Exception as e:
            logger.error(f"GPIO setup failed: {str(e)}")
    
    def button_callback(self, channel):
        """Callback function for button press events."""
        if not self.processing:
            self.button_pressed = True
    
    def set_led_status(self, on: bool):
        """Control the status LED."""
        if GPIO_AVAILABLE:
            GPIO.output(LED_PIN, GPIO.HIGH if on else GPIO.LOW)
    
    def record_audio(self, duration: int = RECORDING_DURATION) -> Optional[str]:
        """
        Record audio from the default microphone and save it as a WAV file.
        """
        try:
            logger.info(f"Recording for {duration} seconds...")
            # Record audio
            recording = sd.rec(
                int(duration * AUDIO_SAMPLE_RATE),
                samplerate=AUDIO_SAMPLE_RATE,
                channels=1,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to complete

            # Save the recording to a WAV file
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
            # The endpoint from the FastAPI server
            url = f"{self.server_url}/analyze-screen/"
            logger.info(f"Sending audio to server: {url}")

            with open(audio_file_path, 'rb') as audio_file:
                files = {'audio_file': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
                
                response = requests.post(url, files=files, timeout=30, stream=True)
                
                if response.status_code == 200:
                    logger.info("Successfully received audio response from server.")
                    # Write the streaming audio response to a file
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
    
    def process_server_response(self, response_audio_path: str) -> bool:
        """
        Play the audio file received from the server.
        """
        if not os.path.exists(response_audio_path):
            logger.error("Response audio file not found.")
            return False
            
        try:
            logger.info(f"Playing response audio: {response_audio_path}")
            # Use mpg123, a command-line MP3 player, to play the response
            os.system(f"mpg123 -q {response_audio_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to play audio response: {e}")
            return False
    
    def check_server_health(self) -> bool:
        """
        Check if the server is reachable by pinging its root URL.
        """
        try:
            # The root URL of our FastAPI server serves as a simple health check
            url = f"{self.server_url}/"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            logger.error(f"Server at {self.server_url} is not reachable.")
            return False
    
    def cleanup(self):
        """Clean up temporary audio files."""
        for path in [TEMP_RECORDING_PATH, TEMP_RESPONSE_PATH]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError as e:
                    logger.warning(f"Could not clean up file {path}: {e}")

    def run_voice_command_cycle(self):
        """
        Run a complete voice command cycle: record -> send -> process response.
        """
        self.processing = True
        self.set_led_status(True) # LED ON: indicates processing
        
        try:
            if not self.check_server_health():
                return
            
            # 1. Record audio
            recorded_file = self.record_audio()
            if not recorded_file:
                return

            # 2. Send to server and get audio response back
            response_file = self.send_audio_to_server(recorded_file)
            if not response_file:
                return

            # 3. Play the server's audio response
            self.process_server_response(response_file)
            
        finally:
            self.processing = False
            self.set_led_status(False) # LED OFF: cycle finished
            self.cleanup()
            logger.info("Cycle finished. Ready for next command.")
    
    def run_continuous_mode(self):
        """Run the controller in continuous mode, waiting for button presses."""
        if not GPIO_AVAILABLE:
            logger.error("GPIO not available - cannot run in continuous mode.")
            return
        
        logger.info("Starting continuous mode. Press the button to start recording.")
        try:
            while True:
                if self.button_pressed:
                    self.button_pressed = False # Reset the flag
                    self.run_voice_command_cycle()
                time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Continuous mode interrupted.")
        finally:
            self.cleanup_gpio()
    
    def cleanup_gpio(self):
        """Clean up GPIO resources."""
        if GPIO_AVAILABLE:
            GPIO.cleanup()
            logger.info("GPIO cleanup complete.")

def main():
    controller = PiAudioController()
    
    # Default to continuous mode if GPIO is available
    if GPIO_AVAILABLE:
        controller.run_continuous_mode()
    else:
        # Fallback to a single run for testing without hardware
        logger.info("Running a single cycle (no GPIO detected).")
        controller.run_voice_command_cycle()

if __name__ == "__main__":
    main()