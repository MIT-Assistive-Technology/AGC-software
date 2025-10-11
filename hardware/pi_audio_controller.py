#!/usr/bin/env python3
"""
Raspberry Pi Zero W Audio Controller Script

This script runs on a Raspberry Pi Zero W and provides voice control
functionality for our controller by:
1. Recording audio from microphone
2. Sending audio to the local server
3. Processing the response using voice response functions

Hardware Requirements:
- Raspberry Pi Zero W
- USB microphone or audio input device
- Network connection to our local server

Dependencies:
- requests (for HTTP communication)
"""

import os
import sys
import time
import requests
import logging
from typing import Optional, Dict, Any

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Button functionality will be disabled.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVER_HOST = "192.168.1.100"  
SERVER_PORT = 8000
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
RECORDING_DURATION = 5  # seconds
MAX_RETRIES = 3

# GPIO Configuration
BUTTON_PIN = 18  # GPIO pin for the push button
LED_PIN = 24     # GPIO pin for status LED
BUTTON_DEBOUNCE_TIME = 200  # milliseconds


class PiAudioController:
    """Main controller class for Raspberry Pi audio operations."""
    
    def __init__(self, server_host: str = SERVER_HOST, server_port: int = SERVER_PORT):
        self.server_url = f"http://{server_host}:{server_port}"
        self.audio_file_path = None
        self.button_pressed = False
        self.processing = False
        self.gpio_setup = False
        
        # Setup GPIO if available
        if GPIO_AVAILABLE:
            self.setup_gpio()
    
    def setup_gpio(self):
        """Setup GPIO pins for button and LED."""
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Setup button pin (with pull-up resistor)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Setup LED pin
            GPIO.setup(LED_PIN, GPIO.OUT)
            GPIO.output(LED_PIN, GPIO.LOW)
            
            # Add event detection for button press
            GPIO.add_event_detect(
                BUTTON_PIN, 
                GPIO.FALLING, 
                callback=self.button_callback,
                bouncetime=BUTTON_DEBOUNCE_TIME
            )
            
            self.gpio_setup = True
            logger.info(f"GPIO setup complete - Button: GPIO{BUTTON_PIN}, LED: GPIO{LED_PIN}")
            
        except Exception as e:
            logger.error(f"GPIO setup failed: {str(e)}")
            self.gpio_setup = False
    
    def button_callback(self, channel):
        """Callback function for button press events."""
        if not self.processing:
            logger.info("Button pressed - starting voice command cycle")
            self.button_pressed = True
            self.set_led_status(True)  # Turn on LED to indicate processing
        else:
            logger.info("Button pressed but already processing - ignoring")
    
    def set_led_status(self, on: bool):
        """Control the status LED."""
        if GPIO_AVAILABLE and self.gpio_setup:
            try:
                GPIO.output(LED_PIN, GPIO.HIGH if on else GPIO.LOW)
            except Exception as e:
                logger.error(f"LED control error: {str(e)}")
    
    def wait_for_button_press(self) -> bool:
        """Wait for button press or return immediately if already pressed."""
        if self.button_pressed:
            self.button_pressed = False
            return True
        
        logger.info("Waiting for button press...")
        while not self.button_pressed: # we might change this to a timeout
            time.sleep(0.1)
        
        self.button_pressed = False
        return True
        
    def record_audio(self, duration: int = RECORDING_DURATION) -> Optional[str]:
        """
        Record audio from microphone and save to temporary file.
        Should be calling the voice_input module
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to recorded audio file, or None if failed
        """
        raise NotImplementedError("should be calling the voice_input module")
    
    def send_audio_to_server(self, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """
        Send audio file to the local server for processing.
       
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Server response as dictionary (or a voice file if we move the TTS to the server side), or None if failed 
        """
        try:
            url = f"{self.server_url}/audio/process"
            logger.info(f"Sending audio to server: {url}")
            with open(audio_file_path, 'rb') as audio_file:
                files = {'audio_file': audio_file}
                
                response = requests.post(
                    url,
                    files=files,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info("Successfully received response from server")
                    return result
                else:
                    logger.error(f"Server error: {response.status_code} - {response.text}")
                    return None
                    
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to server at {self.server_url}")
            return None
        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return None
        except Exception as e:
            logger.error(f"Error sending audio to server: {str(e)}")
            return None
    
    def process_server_response(self, response: Dict[str, Any]) -> bool:
        """
        Process the server response using voice response module.
        
        Args:
            response: Server response dictionary
            
        Returns:
            True if processing successful, False otherwise
        """
        raise NotImplementedError("should be calling the voice_response module")
    
    
    def check_server_health(self) -> bool:
        """
        Check if the server is healthy and reachable.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            url = f"{self.server_url}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"Server health check passed: {health_data.get('status', 'unknown')}")
                return True
            else:
                logger.error(f"Server health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Server health check error: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.audio_file_path and os.path.exists(self.audio_file_path):
            try:
                os.unlink(self.audio_file_path)
                logger.info("Cleaned up temporary audio file")
            except Exception as e:
                logger.warning(f"Could not clean up audio file: {str(e)}")
    
    def run_voice_command_cycle(self) -> bool:
        """
        Run a complete voice command cycle: record -> send -> process.
        
        Returns:
            True if cycle completed successfully, False otherwise
        """
        try:
            self.processing = True
            logger.info("Starting voice command cycle...")
            
            # Check server health first
            if not self.check_server_health():
                logger.error("Server is not healthy, aborting cycle")
                return False
            
            # Record audio
            audio_file = self.record_audio()
            if not audio_file:
                logger.error("Failed to record audio")
                return False
            
            # Send to server
            response = self.send_audio_to_server(audio_file)
            if not response:
                logger.error("Failed to get response from server")
                return False
            
            # Process response
            success = self.process_server_response(response)
            if not success:
                logger.error("Failed to process server response")
                return False
            
            logger.info("Voice command cycle completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in voice command cycle: {str(e)}")
            return False
        finally:
            self.processing = False
            self.set_led_status(False)  # Turn off LED when done
            self.cleanup()
    
    def run_continuous_mode(self):
        """Run the controller in continuous mode, waiting for button presses."""
        logger.info("Starting continuous mode - waiting for button presses...")
        
        if not GPIO_AVAILABLE:
            logger.error("GPIO not available - cannot run in continuous mode")
            return
        
        try:
            while True:
                # Wait for button press
                if self.wait_for_button_press():
                    # Run voice command cycle
                    success = self.run_voice_command_cycle()
                    
                    if success:
                        logger.info("Voice command completed successfully")
                    else:
                        logger.error("Voice command failed")
                    
                    # Brief pause before ready for next command
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Continuous mode interrupted by user")
        except Exception as e:
            logger.error(f"Error in continuous mode: {str(e)}")
        finally:
            self.cleanup_gpio()
    
    def cleanup_gpio(self):
        """Clean up GPIO resources."""
        if GPIO_AVAILABLE and self.gpio_setup:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.error(f"GPIO cleanup error: {str(e)}")


def main():
    """Main function to run the Pi audio controller."""
    logger.info("Starting Raspberry Pi Audio Controller")
    
    # Check if we're running on a Pi (optional check)
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM2835' in cpuinfo or 'BCM2836' in cpuinfo or 'BCM2837' in cpuinfo:
                logger.info("Running on Raspberry Pi")
            else:
                logger.warning("Not running on Raspberry Pi - some features may not work")
    except:
        logger.warning("Could not detect Raspberry Pi hardware")
    
    # Initialize controller
    controller = PiAudioController()
    
    try:
        # Check command line arguments for mode
        if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
            # Run in continuous mode (wait for button presses)
            controller.run_continuous_mode()
        else:
            # Run single voice command cycle (for testing)
            logger.info("Running single voice command cycle (use --continuous for button mode)")
            success = controller.run_voice_command_cycle()
            
            if success:
                logger.info("Voice command cycle completed successfully")
                sys.exit(0)
            else:
                logger.error("Voice command cycle failed")
                sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        controller.cleanup_gpio()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        controller.cleanup_gpio()
        sys.exit(1)


if __name__ == "__main__":
    main()
