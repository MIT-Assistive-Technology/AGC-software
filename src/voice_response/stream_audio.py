# text-to-speech

import numpy as np
from piper import PiperVoice, SynthesisConfig
import sounddevice as sd # need to install
import threading
import queue

# customize voice
syn_config = SynthesisConfig( 
    volume=1.0,  # volume; default = 1.0
    length_scale=1.0,  # length of speech; < 1.0 means faster, > 1.0 means slower; default=1.0
    noise_scale=0.667,  # amount of generator noise; default=0.667
    noise_w_scale=0.8,  # amount of randomness in speed; default=0.8
    normalize_audio=True, # stabilizes audio output
    speaker_id=2 # chooses which speaker to use; relevant only for multi-speaker models 
)

q = queue.Queue()
leftover = []

def audio_callback(outdata, frames, time_info, status): # continuously feed audio data into stream
    if status:
        print(status)
    
    global leftover # leftover audio from long chunks
    if len(leftover) != 0: # first priority: get from leftover
        data = leftover.copy()
        leftover = []
    elif not q.empty(): # get from queue
        data = q.get_nowait()
    else: # no data anywhere -> silence
        outdata[:] = np.zeros((frames, 1))
        return

    #print("I need " + str(frames) + " frames, and you are giving me " + str(len(data)))
    
    if len(data) < frames: # chunk too short -> pad with zeros
        need = frames-len(data)
        if q.empty(): # no more data -> zeroes
            data = np.append(data, np.zeros(need))
        else: # there is more data -> get more data to fill empty space
            extraData = q.get_nowait()
            assert(len(extraData) > frames) # is probably true, each chunk is pretty long
            assert(len(leftover) == 0) # shouldn't write over anything
            data = np.append(data, extraData[:need])
            leftover = extraData[need:].copy()
    elif len(data) > frames: # chunk too long -> truncate & put the rest in leftover
        leftover = data[frames:].copy()
        data = data[:frames].copy()
    
    assert len(data) == frames
    outdata[:] = data.reshape(-1, 1).copy()


def addAudio(text = "this is a test. 1 2 3. 4 5 6. 7 8 9."): # add audio to the end of queue
    #voice = PiperVoice.load(voiceStr)
    for chunk in voice.synthesize(text, syn_config=syn_config):
        audio_data = np.frombuffer(chunk.audio_int16_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        q.put(audio_data)

def startStream(): # initialize audio stream
    global stream
    stream = sd.OutputStream(samplerate=voice.config.sample_rate, channels=1, callback=audio_callback)
    stream.start()
    q.join()

#ukrainian model: uk_UA-ukrainian_tts-medium.onnx
def prepareVoice(voiceStr = "en_US-lessac-medium.onnx"): # initialize voice
    global voice
    voice = PiperVoice.load(voiceStr)

def pauseStream(): # pause audio
    stream.stop()

def resumeStream(): # resumes audio
    stream.start()

def clearStream(): # clear queued text
    global leftover
    leftover = []
    while q.empty() == False:
        q.get_nowait()

def testCommands(): # test usable commands
    print("Enter text to speak, 1 to stop, 2 to resume, 3 to clear queued text")
    while True:
        text = input("Enter selection: ")
        if text == "1":
            pauseStream()
        elif text == "2":
            resumeStream()
        elif text == "3":
            clearStream()
        else:
            addAudio(text)

prepareVoice()
addAudio("hello") # You need an initial text to make it keep working, trust
threading.Thread(target=startStream).start()

#testCommands() # uncomment to test usable commands