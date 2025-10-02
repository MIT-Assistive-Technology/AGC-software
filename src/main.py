#!/usr/bin/env python3
"""
Main entry point for the Adaptive Gaming Controller software.

This module initializes and coordinates all components of the AGC system.
"""

import asyncio
import signal
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config.settings import Settings
from voice_input.hotkey_listener import HotkeyListener
from screen_capture.screenshot import ScreenCapture
from ai_agent.image_analyzer import ImageAnalyzer
from voice_response.text_to_speech import TextToSpeech


class AGCApplication:
    """Main application class that coordinates all AGC components."""
    
    def __init__(self):
        """Initialize the AGC application."""
        self.settings = Settings()
        self.setup_logging()
        
        # Initialize components
        self.hotkey_listener: Optional[HotkeyListener] = None
        self.screen_capture: Optional[ScreenCapture] = None
        self.image_analyzer: Optional[ImageAnalyzer] = None
        self.tts: Optional[TextToSpeech] = None
        
        self.running = False
        
    def setup_logging(self):
        """Configure logging for the application."""
        logger.remove()  # Remove default handler
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=self.settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>"
        )
        
        # Add file handler if specified
        if self.settings.log_file:
            log_path = Path(self.settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_path,
                level=self.settings.log_level,
                rotation=self.settings.log_rotation,
                retention="1 week",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            )
    
    async def initialize_components(self):
        """Initialize all AGC components."""
        logger.info("Initializing AGC components...")
        
        try:
            # Initialize components in dependency order
            self.tts = TextToSpeech(self.settings)
            self.screen_capture = ScreenCapture(self.settings)
            self.image_analyzer = ImageAnalyzer(self.settings)
            self.hotkey_listener = HotkeyListener(
                self.settings,
                self.on_voice_activation
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def on_voice_activation(self):
        """Handle voice activation event."""
        logger.info("Voice activation detected")
        
        try:
            # Take screenshot
            screenshot = await self.screen_capture.capture()
            if not screenshot:
                await self.tts.speak("Unable to capture screen")
                return
            
            # Analyze image with AI
            analysis = await self.image_analyzer.analyze(screenshot)
            if not analysis:
                await self.tts.speak("Unable to analyze screen content")
                return
            
            # Provide audio feedback
            await self.tts.speak(analysis.description)
            
        except Exception as e:
            logger.error(f"Error processing voice activation: {e}")
            await self.tts.speak("An error occurred while processing your request")
    
    async def start(self):
        """Start the AGC application."""
        logger.info("Starting Adaptive Gaming Controller...")
        
        try:
            await self.initialize_components()
            
            # Start components
            await self.hotkey_listener.start()
            await self.screen_capture.start()
            
            self.running = True
            logger.info("AGC is now running. Press Ctrl+C to stop.")
            
            # Keep the application running
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the AGC application."""
        logger.info("Stopping AGC application...")
        
        self.running = False
        
        # Stop components in reverse order
        if self.hotkey_listener:
            await self.hotkey_listener.stop()
        
        if self.screen_capture:
            await self.screen_capture.stop()
        
        logger.info("AGC application stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    app = AGCApplication()
    app.setup_signal_handlers()
    
    try:
        await app.start()
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the application
    asyncio.run(main())
