import sounddevice as sd
import numpy as np

def audio_callback(indata, frames, time, status):
    volume = np.linalg.norm(indata) * 10
    print(round(volume, 2))

with sd.InputStream(callback=audio_callback):
    print("Listening...")
    input("Press Enter to stop...\n")