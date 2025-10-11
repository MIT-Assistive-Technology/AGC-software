# Adaptive Gaming Controller (AGC) Software

A voice-controlled accessibility assistant that helps blind users navigate and interact with games through AI-powered screen analysis and voice commands.

## Project Overview

This software runs alongside games to provide real-time accessibility support for blind users. Users can:
- Press a key to activate voice input
- Ask to hear all available options on screen
- Select specific UI elements through voice commands
- Receive audio descriptions of game states and menus

The system uses AI to analyze screenshots, understand game interfaces, and provide intelligent voice responses.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Input   │    │  Screen Capture │    │ Voice Response  │
│                 │    │                 │    │                 │
│ • Hotkey detect │    │ • Screenshot    │    │ • Text-to-Speech│
│ • Speech-to-Text│    │ • Game detection│    │ • Audio output  │
│ • Command parse │    │ • Image process │    │ • Response queue│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AI Agent      │
                    │                 │
                    │ • Image analysis│
                    │ • UI detection  │
                    │ • Command proc. │
                    │ • Response gen. │
                    └─────────────────┘
```

## Project Structure

```
AGC-software/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
│
├── src/                         # Main source code
│   ├── __init__.py
│   ├── main.py                  # Application entry point
│   ├── config/                  # Configuration management
│   ├── voice_input/             # Voice input processing
│   ├── screen_capture/          # Screen capture and analysis
│   ├── ai_agent/                # AI processing and decision making
│   ├── local_server/            # Local server API with FastAPI
│   ├── voice_response/          # Text-to-speech and audio output
│   └── utils/                   # Shared utilities
│
├── tests/                       # Test suites
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── fixtures/                # Test data and mock files
│
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── architecture/            # System design docs
│   ├── user_guide/              # User documentation
│   └── development/             # Development guides
│
├── scripts/                     # Development and deployment scripts
│   ├── setup_dev.py             # Development environment setup
│   ├── run_tests.py             # Test runner
│   └── build.py                 # Build scripts
│
├── data/                        # Data files
│   ├── models/                  # AI models and weights
│   ├── audio/                   # Audio samples and templates
│   └── game_configs/            # Game-specific configurations
│
└── hardware/                    # Hardware integration
    ├── pi_audio_controller.py   # Raspberry Pi Zero W audio controller
    ├── setup_pi.sh              # Pi setup script
    ├── README.md                # Hardware documentation
    ├── microchip/               # Microchip code (future)
    ├── controller/              # Controller firmware (future)
    └── specs/                   # Hardware specifications
```

## Quick Start

### Prerequisites
- Python 3.8+
- Microphone access
- Screen capture permissions
- OpenAI API key (or alternative AI service)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd AGC-software

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys and settings
nano .env

# Run setup script
python scripts/setup_dev.py

# Start the application
python src/main.py
```

## Component Breakdown

### 1. Voice Input (`src/voice_input/`)
**Team Members: 1-2 developers**
- **Responsibility**: Handle hotkey detection, speech-to-text conversion, and command parsing
- **Key Files**:
  - `hotkey_listener.py` - Global hotkey detection
  - `speech_to_text.py` - Convert speech to text
  - `command_parser.py` - Parse user commands
- **Dependencies**: `pynput`, `speech_recognition`, `pyaudio`

### 2. Screen Capture (`src/screen_capture/`)
**Team Members: 1-2 developers**
- **Responsibility**: Capture screenshots, detect active games, and preprocess images
- **Key Files**:
  - `screenshot.py` - Take and manage screenshots
  - `game_detector.py` - Identify running games
  - `image_processor.py` - Image preprocessing for AI
- **Dependencies**: `pillow`, `pyautogui`, `opencv-python`

### 3. AI Agent (`src/ai_agent/`)
**Team Members: 2-3 developers**
- **Responsibility**: Analyze images, understand UI elements, process commands, generate responses
- **Key Files**:
  - `image_analyzer.py` - Analyze screenshots with AI
  - `ui_detector.py` - Detect UI elements and options
  - `command_processor.py` - Process user commands
  - `response_generator.py` - Generate appropriate responses
- **Dependencies**: `openai`, `transformers`, `torch`, `opencv-python`

### 4. Voice Response (`src/voice_response/`)
**Team Members: 1 developer**
- **Responsibility**: Convert text to speech and manage audio output
- **Key Files**:
  - `text_to_speech.py` - TTS conversion
  - `audio_manager.py` - Audio output management
  - `response_queue.py` - Queue and prioritize responses
- **Dependencies**: `pyttsx3`, `pygame`

### 5. Game Integration (`src/game_integration/`)
**Team Members: 1-2 developers**
- **Responsibility**: Game-specific configurations and optimizations
- **Key Files**:
  - `game_configs.py` - Game-specific settings
  - `ui_templates.py` - Common UI patterns
  - `integration_manager.py` - Manage game integrations
- **Dependencies**: Game-specific libraries as needed

### 6. Local Server (`src/local_server/`)
**Team Members: 1 developer**
- **Responsibility**: Host a local FastAPI server that exposes AGC functions for external devices to query or control
- **Key Files**:
  - `app.py` - FastAPI application with audio processing and health endpoints
  - `README.md` - API documentation and usage examples
- **Endpoints**: 
  - `POST /audio/process` - Upload audio file and receive analysis results
  - `GET /health` - Server status and monitoring
- **Dependencies**: `fastapi`, `uvicorn`, `python-multipart`
- **Entry**: `python -m src.local_server.app` or `uvicorn src.local_server.app:app`

### 7. Hardware Integration (`hardware/`)
**Team Members: 1-2 developers**
- **Responsibility**: Raspberry Pi Zero W controller for physical voice input
- **Key Files**:
  - `pi_audio_controller.py` - Main Pi controller with GPIO button and LED
  - `setup_pi.sh` - Automated Pi setup script
  - `README.md` - Hardware documentation and wiring guide
- **Features**: 
  - Button-triggered audio recording
  - LED status feedback
  - HTTP communication with local server
  - Continuous mode operation
- **Dependencies**: `RPi.GPIO`, `pyaudio`, `requests`
- **Hardware**: Raspberry Pi Zero W, push button, LED, USB microphone

## Development Workflow

### Getting Started
1. Choose a component to work on
2. Read the component's README in its directory
3. Set up your development environment
4. Create a feature branch: `git checkout -b feature/component-name-feature`
5. Implement your changes with tests
6. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Write docstrings for all functions and classes
- Include unit tests for new functionality
- Use type hints where appropriate
- Keep functions small and focused

### Testing
```bash
# Run all tests
python scripts/run_tests.py

# Run specific component tests
python -m pytest tests/unit/voice_input/

# Run integration tests
python -m pytest tests/integration/
```
# Our Team:
- Aurora
- Rachel Yeung
- Matthew
- Wade Rogers
- Erik Xie
- Mellanie Rodriguez
- Maggie Zhang
- Rojina Adhikari
