"""
Configuration settings for the AGC application.

This module handles loading and validating configuration from environment variables.
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # AI Service Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4-vision-preview", env="OPENAI_MODEL")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Voice Configuration
    voice_activation_key: str = Field("f1", env="VOICE_ACTIVATION_KEY")
    speech_recognition_timeout: float = Field(5.0, env="SPEECH_RECOGNITION_TIMEOUT")
    speech_recognition_phrase_timeout: float = Field(1.0, env="SPEECH_RECOGNITION_PHRASE_TIMEOUT")
    tts_rate: int = Field(200, env="TTS_RATE")
    tts_volume: float = Field(0.9, env="TTS_VOLUME")
    
    # Screen Capture Configuration
    screenshot_interval: float = Field(0.5, env="SCREENSHOT_INTERVAL")
    image_quality: int = Field(85, env="IMAGE_QUALITY")
    capture_region_auto: bool = Field(True, env="CAPTURE_REGION_AUTO")
    
    # Audio Configuration
    audio_device_index: int = Field(-1, env="AUDIO_DEVICE_INDEX")
    sample_rate: int = Field(44100, env="SAMPLE_RATE")
    channels: int = Field(1, env="CHANNELS")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field("logs/agc.log", env="LOG_FILE")
    log_rotation: str = Field("10MB", env="LOG_ROTATION")
    
    # Development Settings
    debug_mode: bool = Field(False, env="DEBUG_MODE")
    save_screenshots: bool = Field(False, env="SAVE_SCREENSHOTS")
    save_audio_recordings: bool = Field(False, env="SAVE_AUDIO_RECORDINGS")
    
    # Game Integration
    supported_games: str = Field("all", env="SUPPORTED_GAMES")
    game_detection_method: str = Field("window_title", env="GAME_DETECTION_METHOD")
    
    # Performance Settings
    max_concurrent_requests: int = Field(3, env="MAX_CONCURRENT_REQUESTS")
    response_cache_size: int = Field(100, env="RESPONSE_CACHE_SIZE")
    image_processing_threads: int = Field(2, env="IMAGE_PROCESSING_THREADS")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("voice_activation_key")
    def validate_activation_key(cls, v):
        """Validate voice activation key."""
        valid_keys = [
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
            "ctrl+space", "alt+space", "shift+space", "ctrl+alt+v"
        ]
        if v.lower() not in valid_keys:
            raise ValueError(f"Activation key must be one of: {valid_keys}")
        return v.lower()
    
    @validator("tts_volume")
    def validate_volume(cls, v):
        """Validate TTS volume."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("TTS volume must be between 0.0 and 1.0")
        return v
    
    @validator("image_quality")
    def validate_image_quality(cls, v):
        """Validate image quality."""
        if not 1 <= v <= 100:
            raise ValueError("Image quality must be between 1 and 100")
        return v
    
    @property
    def supported_games_list(self) -> List[str]:
        """Get supported games as a list."""
        if self.supported_games.lower() == "all":
            return ["all"]
        return [game.strip() for game in self.supported_games.split(",")]
    
    def get_data_dir(self) -> Path:
        """Get the data directory path."""
        return Path(__file__).parent.parent.parent / "data"
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory path."""
        if self.log_file:
            return Path(self.log_file).parent
        return Path(__file__).parent.parent.parent / "logs"
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.get_data_dir().mkdir(parents=True, exist_ok=True)
        self.get_logs_dir().mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.get_data_dir() / "models").mkdir(exist_ok=True)
        (self.get_data_dir() / "audio").mkdir(exist_ok=True)
        (self.get_data_dir() / "game_configs").mkdir(exist_ok=True)
        
        if self.save_screenshots:
            (self.get_data_dir() / "screenshots").mkdir(exist_ok=True)
        
        if self.save_audio_recordings:
            (self.get_data_dir() / "audio" / "recordings").mkdir(exist_ok=True)
