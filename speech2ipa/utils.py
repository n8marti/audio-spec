"""General utility functions that don't fit elsewhere."""

import ffmpeg
import math
import numpy as np
import wave

from pathlib import Path


def get_input_file_properties(input_file):
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
    file_info = get_input_file_properties(input_file)
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

def get_input_path_obj(infile_str):
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

def convert_to_np_frames(byte_frames, start, end):
    np_frames = np.frombuffer(byte_frames, dtype='int16')
    np_frames = np_frames[start:end]
    return np_frames

def get_min_amp(frequency):
    """Return the minimum usable amplitude for a given frequency."""
    # Empirically calculated if amp = 20000 is good at 200 Hz; 100 @ 8000 Hz
    #   equation graphing: https://www.desmos.com/calculator

    if frequency <= 2500:
        min_amp = 30000 - 4000 * frequency**(1/4)
        #min_amp = 30000 - 10 * frequency
    else:
        min_amp = 500 - 0.05 * frequency

    #min_amp = 20
    #min_amp = -4000*(frequency - 2500)**(1/9) + 11000
    #min_amp = -1000 * math.log(frequency) + 5000
    #min_amp = 500 - 0.05 * frequency

    return min_amp

def get_peak_amps(amps):
    peaks = []
    amp_1prev = None
    amp_2prev = None
    for i, amp in enumerate(amps):
        if (amp_2prev and amp < amp_1prev and amp_1prev > amp_2prev) \
            or (not amp_2prev and amp_1prev and amp < amp_1prev):
            peaks.append(amp_1prev)
        if amp_1prev:
            amp_2prev = amp_1prev
        amp_1prev = amp
    return peaks

def get_peak_amps_range(amps):
    peaks = get_peak_amps(amps)
    peak_amps_range = max(peaks) - min(peaks)
    return peak_amps_range

def generate_sine_wave(freq, sample_rate, duration):
    x = np.linspace(0, duration, sample_rate * duration, endpoint=False)
    frequencies = x * freq
    # 2pi because np.sin takes radians
    y = np.sin((2 * np.pi) * frequencies)
    return x, y
