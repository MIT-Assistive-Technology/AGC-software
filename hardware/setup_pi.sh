#!/bin/bash
# Setup script for Raspberry Pi Zero W Audio Controller

set -e

echo "Setting up AGC Pi Audio Controller..."

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install audio dependencies
echo "Installing audio dependencies..."
sudo apt-get install -y portaudio19-dev python3-pyaudio alsa-utils

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install requests pyaudio RPi.GPIO

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/pi-audio-controller.service > /dev/null <<EOF
[Unit]
Description=AGC Pi Audio Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/AGC-software
ExecStart=/usr/bin/python3 /home/pi/AGC-software/hardware/pi_audio_controller.py --continuous
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
echo "Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable pi-audio-controller

# Make script executable
chmod +x /home/pi/AGC-software/hardware/pi_audio_controller.py

# Test audio setup
echo "Testing audio setup..."
if arecord -l | grep -q "card"; then
    echo "Audio devices detected:"
    arecord -l
else
    echo "WARNING: No audio devices detected!"
fi

echo "Setup complete!"
echo "To start the service: sudo systemctl start pi-audio-controller"
echo "To check status: sudo systemctl status pi-audio-controller"
echo "To view logs: journalctl -u pi-audio-controller -f"
