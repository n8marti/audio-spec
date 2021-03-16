#!/usr/bin/env python3
"""Read and parse info from audio files."""

import ffmpeg
import sys
import wave
import numpy as np
import matplotlib.ticker as ticker

from matplotlib import pyplot
from pathlib import Path
from scipy.fft import irfft, rfft, rfftfreq


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

def plot_spectrogram(frame_rate, np_frames, input_file, output_file):
    """Plot spectrogram to new window and to PNG file."""
    plt_specgram = pyplot

    # Set format details for plot.
    fig = plt_specgram.figure(num=None, figsize=(12, 7.5), dpi=300)
    ax = fig.add_subplot(111)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(2000))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(500))
    ax.tick_params(axis='both', direction='inout')
    plt_specgram.title(f"Spectrogram of:\n{input_file}")
    plt_specgram.xlabel('Time (seconds)')
    plt_specgram.ylabel('Frequency (Hz)')

    # Set NFFT so that there are ~100 columns per second of audio.
    columns_per_sec = 100   # desired horizontal resolution
    noverlap = 500          # default: 128; correlates with vertical resolution
    # matplotlib says that an NFFT that is a power of 2 is most efficient,
    #   but how would I round the calculation to the nearest power of 2?
    NFFT = int(frame_rate / columns_per_sec + noverlap)

    # Create the plot.
    spectrum, frequencies, times, img = plt_specgram.specgram(
        np_frames,
        Fs=frame_rate,
        cmap='gnuplot',
        noverlap=noverlap,
        NFFT=NFFT,
    )
    ax.set_ylim(None, 8000)
    cbar = plt_specgram.colorbar()
    cbar.ax.set_ylabel('dB')

    # Save the plot to file & show.
    plt_specgram.savefig(output_file)
    #plt_specgram.show()
    #print(len(np_frames))
    #print(len(spectrum.flat))
    #print(len(spectrum), len(spectrum[0]))
    return spectrum, frequencies, times, img

def plot_waveform(frame_rate, np_frames, output_file):
    """Plot raw frame data values to new window and to PNG file."""
    plt_waveform = pyplot

    x, y = [], []
    for i, f in enumerate(np_frames):
        x.append((i + 1) / frame_rate)
        y.append(f)

    # Create the plot.
    fig = plt_waveform.figure(num=None, figsize=(12, 7.5), dpi=100)
    #plt_waveform.scatter(x, y, marker='.', s=0.1)
    plt_waveform.plot(x, y, marker=',', ms=1)

    # Save the plot to file & show.
    plt_waveform.savefig(output_file)
    #plt_waveform.show()

def plot_fourier(frame_rate, np_frames, output_file):
    """Plot Fourier Transformation of audio sample."""
    plt_fourier = pyplot
    n = len(np_frames)
    #norm_frames = np.int16((byte_frames / byte_frames.max()) * 32767)

    yf = rfft(np_frames)
    xf = rfftfreq(n, 1 / frame_rate)

    fig = plt_fourier.figure(num=None, figsize=(12, 7.5), dpi=100)
    plt_fourier.plot(xf, np.abs(yf))
    plt_fourier.savefig(output_file)
    #plt_fourier.show()

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

def cut_high_freqs(spectrum, frequencies, max=8000):
    """Remove frequencies over 8000 Hz from given numpy 2D-array."""
    #print("Cut high freqs:")
    lower_np_spectrum = np.copy(spectrum)
    lower_np_frequencies = np.copy(frequencies)
    for i in range(len(spectrum)):
        if frequencies[i] > max:
            lower_np_spectrum = np.delete(lower_np_spectrum, slice(i, None), 0)
            lower_np_frequencies = np.delete(lower_np_frequencies, slice(i, None), 0)
            break

    #print(len(spectrum), len(lower_np_spectrum))
    #print(len(frequencies), len(lower_np_frequencies))
    return lower_np_spectrum, lower_np_frequencies

def subtract_bg_noise(np_spectrum, np_freqs):
    """Reduce all amplitudes of each frequency by that frequency's minimum amplitude."""
    # Define "background noise":
    #   1. For a given spectrum, the minimum amplitude at each frequency.
    #   2. For a given wave, a relative maximum amplitude seen throughout the clip.
    #   3. For a given spectrum, a roughly constant amplitude at each frequency.
    for i, row in enumerate(np_spectrum):
        for j, amp in enumerate(row):
            np_spectrum[i, j] = amp - min(row)
    return np_spectrum

def show_spectrum_properties(np_spectrum, np_freqs, np_times):
    """Print out insightful properties of the normalized spectrum data."""
    # Duration (s)
    # Frequency range (max 8 kHz)
    duration = round(np_times[-1], 2)
    max_amp_raw = max(np_spectrum.flat)
    min_amp_raw = min(np_spectrum.flat)

    # TODO: Irrelevant: this just picks the highest from the scale, not from data.
    max_freq = round(max(np_freqs), 0)
    min_freq = round(min(np_freqs), 0)

    print(f"Duration: {duration} s")

def normalize_spectrum(np_spectrum, np_freqs):
    """Normalize specturm by applying desired filters."""
    # Trim out high frequencies (> 8 kHz).
    np_spectrum, np_freqs = cut_high_freqs(np_spectrum, np_freqs)
    # Trim out background white noise.
    np_spectrum = subtract_bg_noise(np_spectrum, np_freqs)

    return np_spectrum, np_freqs

def save_wav_as(np_spectrum, file_info, output_file):
    """Write out the wave data to a WAV file."""
    print(np_spectrum.shape)
    np_frames = np_spectrum.flatten()
    print(np_frames.shape)
    byte_frames = np_frames.tobytes()
    with wave.open(str(output_file), 'wb') as wav:
        wav.setparams(file_info)
        #wav.setframerate(frame_rate)
        #wav.setnchannels(1)
        #wav.setsampwidth(2)
        wav.writeframes(byte_frames)

def generate_plots(input_file, np_frames, frame_rate):
    # Generate spectrogram.
    output_file = input_file.with_suffix(".specgram.png")
    np_spectrum, np_freqs, np_times, img_spec = plot_spectrogram(
        frame_rate,
        np_frames,
        input_file,
        output_file,
    )

    # Generate waveform plot.
    output_file = input_file.with_suffix(".waveform.png")
    plot_waveform(
        frame_rate,
        np_frames,
        output_file,
    )

    # Generate plot of Fourier Transformation.
    output_file = input_file.with_suffix(".fourier.png")
    plot_fourier(
        frame_rate,
        np_frames,
        output_file,
    )

    return np_spectrum, np_freqs, np_times


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

# Convert byte_frames to np_frames, limited by start and end args.
np_frames = np.frombuffer(byte_frames[startfr:endfr], dtype='int16')

# Generate illustrative plots; return spectrum.
np_spectrum, np_freqs, np_times = generate_plots(input_file, np_frames, file_info.framerate)

# Normalize specturm by applying filters.
np_spectrum, np_freqs = normalize_spectrum(np_spectrum, np_freqs)

# Output descriptive properties of spectrum.
show_spectrum_properties(np_spectrum, np_freqs, np_times)
