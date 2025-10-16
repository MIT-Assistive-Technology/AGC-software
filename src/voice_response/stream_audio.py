import numpy as np
from piper import PiperVoice, SynthesisConfig
import sounddevice as sd
import threading

# customize voice
syn_config = SynthesisConfig(
    volume=1.0,  # volume; default = 1.0
    length_scale=1.0,  # length of speech; < 1.0 means faster, > 1.0 means slower; default=1.0
    noise_scale=0.667,  # amount of generator noise; default=0.667
    noise_w_scale=0.8,  # amount of randomness in speed; default=0.8
    normalize_audio=True, # stabilizes audio output
    speaker_id=2 # chooses which speaker to use; relevant only for multi-speaker models 
)

stopPlay = False # if True, streaming will stop

# plays speech.
# voiceStr: voice ID of the chosen voice/language (default = english) 
# text: the text to speak
def piperContinuousStream(voiceStr = "en_US-lessac-medium.onnx", text = "this is a test. 1 2 3. 4 5 6. 7 8 9."):
    global stopPlay # use global version of variable (so it can be changed by a function definition)
    stopPlay = False
    voice = PiperVoice.load(voiceStr)
    with sd.OutputStream(samplerate=22050, channels=1, dtype='int16') as stream:
        for chunk in voice.synthesize(text, syn_config=syn_config): # piper TTS parses text into chunks (sentences)
            if stopPlay: # if stopPlay flag is set to True, stop playing
                break
            audio_data = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16) # chunk is converted to playable format
            stream.write(audio_data) # plays chunk of audio


# puts streaming in a thread so other processes can continue. Streaming will end if enter is pressed
# voiceStr: voice ID of the chosen voice/language (default = english) 
# text: the text to speak
# does NOT support multiple calls of playAudio if one of the calls are interrupted
# TODO: use callback() function to continuously feed text to the OutputStream. Hopefully the StopPlay variable becomes unnecessary
def playAudio(voiceStr = "en_US-lessac-medium.onnx", text = "this is a test. 1 2 3. 4 5 6. 7 8 9."): 
    thread = threading.Thread(target=piperContinuousStream,args=(voiceStr,text)) 
    thread.start()

    input("Press enter to stop\n") # TODO: replace with real way to check whether to stop
    global stopPlay
    stopPlay = True