#!/usr/bin/env python3

import numpy as np
import sys
import wave

from pathlib import Path

def generate_sine_wave(frequencies, sample_rate, duration):
    d = int(duration)
    samples = np.linspace(0, d, int(sample_rate) * d, endpoint=False)
    signals = []
    for f in frequencies:
        # 2pi because np.sin takes radians
        signal = np.sin(2 * np.pi * samples * int(f))
        signals.append(signal)
    total_signal = 0
    for s in signals:
        total_signal += s
    combined_signal = total_signal / len(signals)
    combined_signal *= 32767
    combined_signal = np.int16(combined_signal)
    return combined_signal

def save_wave_as(np_frames, frame_rate, output_file):
    """Write out the wave data to a WAV file."""
    byte_frames = np_frames.tobytes()
    with wave.open(str(output_file), 'wb') as wav:
        #wav.setparams(file_info)
        wav.setframerate(frame_rate)
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.writeframes(byte_frames)

if len(sys.argv) == 1:
    print(f"{__file__} freq [freq1 freq2 ...] filename.wav")
    exit(1)

outfile = sys.argv[-1]
freqs = sys.argv[1:-1]
sample_rate = 44100
duration = 3
wave_data = generate_sine_wave(freqs, sample_rate, duration)
save_wave_as(wave_data, sample_rate, Path.home() / outfile)
