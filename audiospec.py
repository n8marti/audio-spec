#!/usr/bin/env python3
"""Read and parse info from audio files."""

import ffmpeg
import os
import sys
import wave
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import subprocess
import shutil

from pathlib import Path
from scipy.fft import irfft, rfft, rfftfreq
from scipy.io import wavfile


def get_full_path_obj(infile_str):
    # Get full path to input file.
    #   .expanduser() expands out possible "~"
    #   .resolve() expands relative paths and symlinks
    input_file = Path(infile_str).expanduser().resolve()
    if not input_file.is_file():
        print(f"Error: invalid input file: {input_file}")
        exit(1)
    return input_file

def get_output_file_obj(infile_obj):
    output_file = input_file.with_name(f"{input_file.stem}.wav")
    return output_file

def get_properties(input_file):
    try:
        probe = ffmpeg.probe(input_file)
    except ffmpeg._run.Error:
        print("Error: Not an audio file?")
        exit(1)
    return probe['streams']

def convert_to_wav(input_file):
    """Convert to WAV. Output to same directory as input_file."""
    # TODO: This needs to be tested.
    #   command = f"ffmpeg -i {input_file} -ar 44100 -ac 1 {output_file}"
    output_file = get_output_file_obj(input_file)

    # Get input file details.
    file_info = get_properties(input_file)
    if file_info:
        audio_streams = [a for a in file_info if a['codec_type'] == 'audio']
    else:
        audio_streams = None

    # Build command sequence.
    stream = ffmpeg.input(str(input_file))
    audio = stream['a']

    # Define other output constants.
    audio_bitrate = 128000
    format = 'wav'
    sample_rate = 44100

    # Tailor command depending on whether there are 0 or 1 audio and video input streams.
    if audio_streams:
        stream = ffmpeg.output(
            audio,
            str(output_file),
            format=format,
            ar=44100,
            #audio_bitrate=audio_bitrate,
        )
    else:
        print(f"Error: No audio streams found in {input_file}.")
        exit(1)

    ffmpeg.run(stream)
    return output_file

def get_wav_info(input_file):
    """Get file info and file data."""
    with wave.open(str(input_file)) as wav:
        file_info = wav.getparams()
        byte_frames = wav.readframes(-1)
    return file_info, byte_frames

def graph_spectrogram(frame_rate, byte_frames, output_file):
    """Plot spectrogram to new window and to PNG file."""

    # Convert byte_frames to np_frames.
    np_frames = np.frombuffer(byte_frames, dtype='int16')

    # Set format details for plot.
    fig = plt.figure(num=None, figsize=(12, 7.5), dpi=150)
    ax = fig.add_subplot(111)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5000))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(1000))
    ax.tick_params(axis='both', direction='inout')
    plt.title(f"Spectrogram of:\n{input_file.name}")
    plt.xlabel('Time (seconds)')
    plt.ylabel('Frequency (kHz)')
    plt.specgram(np_frames, Fs=frame_rate, cmap='gnuplot')
    cbar = plt.colorbar()
    cbar.ax.set_ylabel('dB')

    # Save the plot to file & show.
    plt.savefig(output_file)
    plt.show()

def print_wav_frames(wavinfo, wavframes, startsec, endsec):
    """Print one frame per line from the given time range."""
    # column1 = relative frequency?
    # column2 = relative amplitude?
    print(wavinfo)
    bitrate = 16 # assumed, for now. Found at bytes 35-36 (10 00 = 16).
    len_frame = wavinfo.nchannels * wavinfo.sampwidth
    framerate = wavinfo.framerate
    startfr = int(startsec * framerate)
    endfr = int(endsec * framerate)
    for i, frame in enumerate(wavframes[startfr:endfr]):
        if i % len_frame < len_frame - 1:
            print(f"{frame}\t", end='')
        else:
            print(frame)
    print()

def generate_sine_wave(freq, sample_rate, duration):
    x = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    frequencies = x * freq
    # 2pi because np.sin takes radians
    y = np.sin((2 * np.pi) * frequencies)
    return x, y


# Read arguments; set global variables.
startfr = None
endfr = None
if len(sys.argv) > 1:
    infile_str = sys.argv[1]

    # Convert to WAV if necessary.
    input_file = get_full_path_obj(infile_str)
    if input_file.suffix != '.wav':
        input_file = convert_to_wav(input_file)

    # Retrieve file data.
    file_info, byte_frames = get_wav_info(input_file)

if len(sys.argv) > 2:
    endsec = float(sys.argv[-1])
    endfr = int(endsec * file_info.framerate * file_info.sampwidth)
if len(sys.argv) == 4:
    startsec = float(sys.argv[2])
    startfr = int(startsec * file_info.framerate * file_info.sampwidth)

# Print out frame data.
#print_wav_frames(file_info, byte_frames, startsec, endsec)

# Create spectrogram.
output_file = input_file.with_suffix(".png")
graph_spectrogram(file_info.framerate, byte_frames[startfr:endfr], output_file)

'''
# Generate a 2 hertz sine wave that lasts for 5 seconds
SAMPLE_RATE = 44100  # Hertz
DURATION = 5  # Seconds
BASE_DIR = Path.home() / 'audio-recs'

_, nice_tone = generate_sine_wave(400, SAMPLE_RATE, DURATION)
_, noise_tone = generate_sine_wave(4000, SAMPLE_RATE, DURATION)
noise_tone = noise_tone * 0.3
mixed_tone = nice_tone + noise_tone

# Normalize tone.
normalized_tone = np.int16((mixed_tone / mixed_tone.max()) * 32767)

# Number of samples in normalized_tone
N = SAMPLE_RATE * DURATION


yf = rfft(normalized_tone)
xf = rfftfreq(N, 1 / SAMPLE_RATE)


plt.plot(xf, np.abs(yf))
plt.show()
'''

# Remember SAMPLE_RATE = 44100 Hz is our playback rate
#wavfile.write(BASE_DIR / "mysinewave.wav", SAMPLE_RATE, normalized_tone)
