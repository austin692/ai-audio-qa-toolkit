import numpy as np
import soundfile as sf

audio, sr = sf.read("Austin.wav")
loud = audio * 20
sf.write("loud_test.wav", loud, sr)
