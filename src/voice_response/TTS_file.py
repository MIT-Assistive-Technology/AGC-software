import piper
import wave
import os
# import simpleaudio

syn_config = piper.SynthesisConfig(
    volume=1.0,  # volume; default = 1.0
    length_scale=1.0,  # length of speech; < 1.0 means faster, > 1.0 means slower; default=1.0
    noise_scale=0.667,  # amount of generator noise; default=0.667
    noise_w_scale=0.8,  # amount of randomness in speed; default=0.8
    normalize_audio=True, # stabilizes audio output
    speaker_id=2 # chooses which speaker to use; relevant only for multi-speaker models 
)

def tts_get_pcm(voiceStr = "en_US-lessac-medium.onnx", text = "this is a test. 1 2 3 4 5 6 7 8 9"):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "en_US-lessac-medium.onnx")
    voice = piper.PiperVoice.load(MODEL_PATH)
    with wave.open("piper_output.wav", "wb") as wav_file:
        voice.synthesize_wav(text, wav_file, syn_config=syn_config) # blasdf

    # wave_test = simpleaudio.WaveObject.from_wave_file("piper_output.wav")
    # wave_test = wave_test.play()
    # wave_test.wait_done()

    with wave.open("piper_output.wav", "rb") as wav:
        pcm_data = wav.readframes(wav.getnframes())
    return pcm_data

# print(tts_get_pcm())