# Voice Input Component

**Team Assignment**: 1-2 developers  
**Estimated Time**: 2-3 weeks  
**Dependencies**: `pynput`, `speech_recognition`, `pyaudio`, `keyboard`

## Overview

The Voice Input component handles all aspects of voice-based user interaction:
- Global hotkey detection for voice activation
- Speech-to-text conversion
- Command parsing and interpretation
- Voice command validation

## Architecture

```
Voice Input Flow:
User presses hotkey → HotkeyListener → SpeechToText → CommandParser → AI Agent
```

## Key Files

### `hotkey_listener.py`
- **Purpose**: Detect global hotkey presses to activate voice input
- **Key Functions**:
  - `start()`: Begin listening for hotkey
  - `stop()`: Stop hotkey listener
  - `on_hotkey_pressed()`: Handle hotkey activation
- **Integration**: Triggers speech recognition when activated

### `speech_to_text.py`
- **Purpose**: Convert user speech to text
- **Key Functions**:
  - `listen()`: Start listening for speech
  - `transcribe(audio)`: Convert audio to text
  - `set_timeout(seconds)`: Configure listening timeout
- **Integration**: Provides text to command parser

### `command_parser.py`
- **Purpose**: Parse and validate voice commands
- **Key Functions**:
  - `parse_command(text)`: Extract command and parameters
  - `validate_command(command)`: Ensure command is valid
  - `get_command_type(command)`: Categorize command type
- **Integration**: Sends parsed commands to AI agent

## Implementation Tasks

### Phase 1: Basic Functionality
- [ ] Implement hotkey detection using `pynput`
- [ ] Set up microphone access and audio recording
- [ ] Integrate speech recognition service (Google/OpenAI)
- [ ] Create basic command parsing for common phrases
- [ ] Add error handling for audio device issues

### Phase 2: Enhanced Features
- [ ] Add support for multiple activation keys
- [ ] Implement noise filtering and audio preprocessing
- [ ] Add command history and learning
- [ ] Support for custom voice commands
- [ ] Multi-language support preparation

## API Interface

```python
class VoiceInputManager:
    async def start_listening(self) -> None
    async def stop_listening(self) -> None
    async def process_voice_input(self) -> VoiceCommand
    def set_activation_key(self, key: str) -> None
    def add_custom_command(self, command: str, action: str) -> None
```

## Configuration

```python
# Environment variables used by this component
VOICE_ACTIVATION_KEY=f1
SPEECH_RECOGNITION_TIMEOUT=5
SPEECH_RECOGNITION_PHRASE_TIMEOUT=1
AUDIO_DEVICE_INDEX=-1
SAMPLE_RATE=44100
```

## Testing Strategy

### Unit Tests
- Test hotkey detection with simulated key presses
- Test speech recognition with sample audio files
- Test command parsing with various input formats
- Test error handling for missing audio devices

### Integration Tests
- Test full voice input flow from hotkey to command
- Test with different microphone configurations
- Test command accuracy with various speech patterns

## Common Commands to Support

1. **Navigation Commands**
   - "What's on screen?"
   - "Read all options"
   - "List available buttons"

2. **Selection Commands**
   - "Click [button name]"
   - "Select [option]"
   - "Go to [menu item]"

3. **Information Commands**
   - "Describe this screen"
   - "What can I do here?"
   - "Help me navigate"

## Error Handling

- Microphone not available
- Speech recognition timeout
- Unclear or invalid commands
- Network connectivity issues (for cloud STT)
- Audio device permissions

## Performance Considerations

- Minimize latency between hotkey press and speech recognition start
- Cache speech recognition models locally when possible
- Implement voice activity detection to reduce false triggers
- Optimize audio buffer sizes for responsiveness

## Future Enhancements

- Wake word detection (hands-free activation)
- Voice biometrics for user identification
- Contextual command understanding
- Integration with game-specific vocabularies
