# Local Server Component

This component exposes selected functionality from the AGC application over a local HTTP server so that other devices on the same network can send requests. The server is built using FastAPI and provides RESTful endpoints for audio processing and health monitoring.

## Features

- **Audio Processing Endpoint**: Accepts audio file uploads and returns JSON analysis results
- **Health Check Endpoint**: Provides server status and monitoring information
- **FastAPI Integration**: Automatic API documentation and validation
- **Local Network Access**: Runs on localhost with optional LAN exposure

## Endpoints

### Health Check
- **GET** `/health` - Returns server status, uptime, and request statistics

### Audio Processing
- **POST** `/audio/process` - Upload audio file and receive analysis results
  - Accepts: Audio files (WAV, MP3, etc.)
  - Returns: JSON with transcription, detected commands, and suggested actions

### Root
- **GET** `/` - Basic API information and available endpoints

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Server
```bash
# Run directly
python -m src.local_server.app

# Or using uvicorn directly
uvicorn src.local_server.app:app --host 127.0.0.1 --port 8000

# Access API documentation
# Open http://127.0.0.1:8000/docs in your browser
```

### Example Usage

#### Health Check
```bash
curl http://127.0.0.1:8000/health
```

#### Audio Processing
```bash
curl -X POST "http://127.0.0.1:8000/audio/process" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "audio_file=@example.wav"
```

## Implementation Status

**Current**: Placeholder implementation with mock responses
- Audio endpoint returns structured mock data
- Health endpoint provides real server statistics
- File validation and error handling implemented

**Future Integration Points**:
- Connect to `src/voice_input/` for actual speech-to-text processing
- Integrate with `src/ai_agent/` for command analysis
- Use `src/screen_capture/` for on-demand screenshot analysis
- Add authentication and rate limiting

## Configuration

The server currently runs with default settings:
- Host: `127.0.0.1` (localhost only)
- Port: `8000`
- No authentication (planned for future)

Future configuration options will be added to `src/config/settings.py`:
- `LOCAL_SERVER_ENABLED`
- `LOCAL_SERVER_HOST`
- `LOCAL_SERVER_PORT`
- `LOCAL_SERVER_TOKEN`

## Security Considerations

- Currently runs on localhost only
- No authentication implemented (planned)
- File upload validation in place
- Error handling prevents information leakage
- Logging for audit trail

## Dependencies

- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `python-multipart>=0.0.6` - File upload support

