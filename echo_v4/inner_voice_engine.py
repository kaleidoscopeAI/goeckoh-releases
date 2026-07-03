import pyaudio
import numpy as np
from voice_crystal import VoiceCrystal

class InnerVoiceEngine:
    def __init__(self, voice_crystal: VoiceCrystal):
        self.voice_crystal = voice_crystal

    def deliver_calming_affirmation(self):
        affirmations = ["I am safe.", "I can breathe."]
        audio = self.voice_crystal.synthesize(affirmations[0])
        # Play audio (PyAudio stub)
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=16000, output=True)
        stream.write(audio.astype(np.float32).tobytes()) # Ensure correct format and byte conversion
        stream.stop_stream()
        stream.close()
        p.terminate()