import pyaudio
import wave
import time
from array import array
from struct import pack
import requests
import os
import zipfile

def get_default_device_info():
    p = pyAudio.PyAudio()
    print(f"Default Input: {p.get_default_input_device_info()}")
    print(f"Default Output: {p.get_default_input_device_info()}")
    p.terminate()

def get_input_devices():
    p = pyAudio.PyAudio()
    device_count = p.get_device_count()
    print("Recognized Input Devices:")

    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)

        if device_info.get("maxInputChannels") > 0:
            device_name = device_info.get("name")
            print(f"Index: {i} - Name: {device_name}")

    p.terminate()

def get_output_devices():
    p = pyAudio.PyAudio()
    device_count = p.get_device_count()
    print("Recognized Output Devices")

    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)

        if device_info.get("maxOutputChannels") > 0:
            device_name = device_info.get("name")
            print(f"Index: {i} - Name: {device_name}")

    p.terminate()
def record(output_filename, input_device_index=None):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    DURATION = 5



    p = pyaudio.PyAudio()
    stream = p.open(format = FORMAT,
                    channels = CHANNELS,
                    rate = RATE,
                    input = True,
                    frames_per_buffer = CHUNK,
                    input_device_index = input_device_index)
    print("Recording....")
    frames = []
    for i in range(0, int(RATE/CHUNK * DURATION)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(output_filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b"".join(frames))

    return output_filename

#record.("output2")
p = pyaudio.PyAudio()

print(p.get_default_input_device_info())


#play("output.wav")
timestamp = time.strftime("%Y%m%d_%H%M%S")
wav_filename = f"audio_{timestamp}.wav"

def package_files(files_to_zip, zip_filename):
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            zipf.write(file, os.path.basename(file))
    print(f"Files packaged into {zip_filename}")
    return zip_filename


def play(file, output_device_index=None):
    CHUNK = 1024
    wf = wave.open(file, "rb")
    p = pyaudio.PyAudio()
    stream = p.open(format = p.get_format_from_width(wf.getsampwidth()),
                    channels = wf.getnchannels(),
                    rate = wf.getframerate(),
                    output = True,
                    output_device_index = output_device_index)

    data = wf.readframes(CHUNK)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()
    p.terminate()

def send_to_server(file_path, server_url):
    print(f"Attempting to send {file_path} to {server_url}...")

    if is_ZIP:
        file_type = "application/zip"
    else:
        file_type = "audio/wav"

    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f, {file_type})}

        try:

            response = requests.post(server_url, files = files)

            if response.status_code == 200:
                print("File uploaded successfully.")
                print("Server response:", response.text)
                return True

            else:
                print(f"Upload failed. Status code: {response.status_code}")
                print("Server error:", response.text)
                return False

        except requests.exceptions.RequestException as e:
            print(f"An error occurred during transfer: {e}")
            return False

SERVER_URL = ""
is_ZIP = True

timestamp = time.strftime("%Y%m%d_%H%M%S")
WAV_FILENAME = f"audio_{timestamp}.wav"


if is_ZIP:
    ZIP_FILENAME = f"data_batch_{timestamp}.zip"
else:
    ZIP_FILENAME = f"data_{timestamp}.wav"



recorded = record(WAV_FILENAME)

packaged = package_files([recorded], ZIP_FILENAME)

success = send_to_server(packaged, SERVER_URL)

if success:
    os.remove(recorded_file)
    os.remove(packaged_file)
    print("Local files cleaned up.")
