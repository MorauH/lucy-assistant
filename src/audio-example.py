import sounddevice as sd
import scipy.io.wavfile as wav


# Play TTS output
rate, data = wav.read('src/en_br.wav')
sd.play(data, rate)
sd.wait()
exit()

# Record STT input
duration = 5  # seconds
sample_rate = 44100
recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
sd.wait()

# Save recording and convert
from scipy.io.wavfile import write
write('recording.wav', sample_rate, recording)

