# Raspberry Pi Hardware Integration

This directory contains hardware-specific code for running AGC components on embedded devices, particularly the Raspberry Pi Zero W.

## Components

### Pi Audio Controller (`pi_audio_controller.py`)

A complete voice control system for Raspberry Pi Zero W that:

1. **Records Audio**: Uses PyAudio to capture audio from USB microphone
2. **Sends to Server**: HTTP POST to local server `/audio/process` endpoint
3. **Processes Response**: Calls voice_response functions based on server analysis

#### Hardware Requirements
- Raspberry Pi Zero W
- USB microphone or audio input device
- Push button (momentary switch)
- Status LED (optional)
- Network connection to AGC server
- MicroSD card (8GB+ recommended)

#### Hardware Connections
- **Button**: Connect one terminal to GPIO 18, other to GND (with pull-up resistor)
- **LED**: Connect anode to GPIO 24 through 220Ω resistor, cathode to GND
- **Microphone**: USB microphone or audio input device

#### Software Dependencies
```bash
# Install Python dependencies
pip install requests pyaudio RPi.GPIO

# For audio support on Pi
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio
```

#### Configuration
Edit the configuration variables in `pi_audio_controller.py`:
```python
SERVER_HOST = "192.168.1.100"  # IP of your AGC server
SERVER_PORT = 8000
RECORDING_DURATION = 5  # seconds
```

#### Usage
```bash
# Make executable
chmod +x pi_audio_controller.py

# Run single test cycle (for testing)
python3 pi_audio_controller.py

# Run in continuous mode (waits for button presses)
python3 pi_audio_controller.py --continuous

# Run continuously (with systemd service)
sudo systemctl enable pi-audio-controller
sudo systemctl start pi-audio-controller
```

#### Button Operation
- **Press Button**: Starts audio recording and processing cycle
- **LED On**: Indicates processing is active
- **LED Off**: Ready for next button press
- **Multiple Presses**: Ignored while processing (prevents duplicate commands)

#### Integration Points

**Voice Input Module** (assumes these functions exist):
- Audio recording and file handling
- Integration with `src/voice_input/speech_to_text.py`

**Voice Response Module** (assumes these functions exist):
- `voice_response.read_screen_options()`
- `voice_response.select_option(parameter)`
- `voice_response.describe_screen()`

**Local Server**:
- Sends audio to `POST /audio/process`
- Checks health via `GET /health`

#### Systemd Service Setup

Create `/etc/systemd/system/pi-audio-controller.service`:
```ini
[Unit]
Description=AGC Pi Audio Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/AGC-software
ExecStart=/usr/bin/python3 /home/pi/AGC-software/hardware/pi_audio_controller.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Troubleshooting

**Audio Issues**:
- Check microphone permissions: `lsusb` to verify USB mic
- Test audio: `arecord -l` to list audio devices
- Check PyAudio installation: `python3 -c "import pyaudio; print('OK')"`

**Network Issues**:
- Verify server IP: `ping 192.168.1.100`
- Check server health: `curl http://192.168.1.100:8000/health`
- Test audio upload: Use curl with sample audio file

**Performance**:
- Monitor CPU usage: `htop`
- Check memory: `free -h`
- Review logs: `journalctl -u pi-audio-controller -f`

## Future Hardware Components

### Microchip Integration (`microchip/`)
- Low-level hardware control
- GPIO pin management
- Real-time audio processing

### Controller Firmware (`controller/`)
- Custom controller hardware
- Button mapping and input handling
- Wireless communication protocols

### Hardware Specifications (`specs/`)
- Pinout diagrams
- Power requirements
- Compatibility matrices
