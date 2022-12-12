import math

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
from scipy.io import wavfile

sample_rate, samples = wavfile.read('output.wav')

frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)

print(times)
for frequency in frequencies:
    if frequency > 0:
        pitch = (math.log(int(frequency), 2) - math.log(440, 2)) * 12 + 9
        if abs(pitch - round(pitch)) < 0.2:
            rpitch = int(round(pitch))
            print(rpitch)
            keytable = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "H"]
            note = keytable[rpitch % 12]
            print(note)

time = np.arange(samples.shape[0])
freq = np.fft.fftfreq(time.shape[-1]) * sample_rate

spectrum = np.fft.fft(samples)
print(spectrum.real[275])

# Plot spectrum
plt.plot(freq, abs(spectrum.real))
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude')
plt.title('Spectrum of Recording')
plt.xlim((0, 500))
plt.grid()
plt.show()
