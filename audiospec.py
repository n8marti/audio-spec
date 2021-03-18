#!/usr/bin/env python3
"""Read and parse info from audio files."""

import ffmpeg
import math
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

    '''
    ### This doesn't result in a "narrow" enough bandwidth; i.e. the frequencies
    # Set NFFT so that there are ~100 columns per second of audio.
    #       have too much resolution and each formant is split into multiple
    #       bands.
    columns_per_sec = 100   # desired horizontal resolution
    noverlap = 500          # default: 128; correlates with vertical resolution
    # matplotlib says that an NFFT that is a power of 2 is most efficient,
    #   but how would I round the calculation to the nearest power of 2?
    NFFT = int(frame_rate / columns_per_sec + noverlap) # NFFT = 941
    '''
    # If NFFT is too high, then there the horizontal (frequency) resolution is
    #   too fine, and there are multiple bands for each formant. However, if
    #   NFFT is too low, then the whole image is rather blurry and even the
    #   formants are not well differentiated (i.e. at the fault vaules for NFFT
    #   and noverlap). noverlap that is half of NFFT seems to minimize background
    #   noise, as well.
    noverlap = 256          # default: 128
    NFFT = 512              # default: 256

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

def subtract_bg_noise(np_spectrum, np_freqs, np_times):
    """Reduce the amplitudes of each block deemed to be noise."""
    # Define "background noise":
    #   + For a given spectrum, any amplitude below the average at each frequency.
    #   - For a given spectrum, the minimum amplitude at each frequency.
    #   - For a given wave, a relative maximum amplitude seen throughout the clip.
    for i, row in enumerate(np_spectrum):
        avg_amp = np.average(row)
        min_amp = min(row)
        for j, amp in enumerate(row):
            if amp < avg_amp:
                np_spectrum[i, j] = 0
    return np_spectrum

def show_spectrum_properties(np_spectrum, np_freqs, np_times):
    """Print out insightful properties of the normalized spectrum data."""
    # Duration (s)
    # Frequency range (max 8 kHz)
    duration = round(np_times[-1], 2)
    max_amp_raw = max(np_spectrum.flat)
    min_amp_raw = min(np_spectrum.flat)

    print(f"Duration: {duration} s")

def print_terminal_spectrogram(np_spectrum, np_freqs, np_times, time_frames=False):
    """Print out a basic spectrogram in the terminal for debugging."""
    for ri, r in enumerate(np_spectrum[::-1]):
        # Print frequency scale item.
        if ri % 2 == 0:
            print(f"{int(np_freqs[len(np_freqs) - ri - 1] / 1000)}K ", end='')
        else:
            print('   ', end='')
        # Print frequency rows.
        for a in r:
            if a == 0:
                print('   ', end='')
            elif a < 500:
                print('.  ', end='')
            elif a < VOICE_BASE_AMP:
                print('_  ', end='')
            else:
                print('#  ', end='')
        print()
    # Print time scale.
    dec_places = 1
    shift = 5 / 10 ** ( dec_places + 1 )
    print('  ', end='')
    for i, t in enumerate(np_times):
        if i % 2 == 0:
            if t < shift:
                shift = 0
            print(f"{round(t - shift, dec_places)}   ", end='')
    print()
    if time_frames:
        # Print evaluated properties.
        print()
        # - silence
        print('S: ', end='')
        for time_frame in time_frames.values():
            if time_frame['silence'] == True:
                print('T  ', end='')
            else:
                print('F  ', end='')
        print()
        # - vocalization
        print('V: ', end='')
        for time_frame in time_frames.values():
            if time_frame['vocalization'] == True:
                print('T  ', end='')
            else:
                print('F  ', end='')
        print()
        # - aspiration
        print('A: ', end='')
        for time_frame in time_frames.values():
            if time_frame['aspiration'] == True:
                print('T  ', end='')
            else:
                print('F  ', end='')
        print('\n')

def normalize_spectrum(np_spectrum, np_freqs, np_times):
    """Normalize specturm by applying desired filters."""
    # Trim out high frequencies (> 8 kHz).
    np_spectrum, np_freqs = cut_high_freqs(np_spectrum, np_freqs)
    # Trim out background white noise.
    np_spectrum = subtract_bg_noise(np_spectrum, np_freqs, np_times)

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

def get_amplitudes(time_frame, np_spectrum):
    """Add the amplitude at each frequency to the given time frame."""
    time_frame['amplitudes'] = [row[time_frame['index']] for row in np_spectrum]
    return time_frame

def get_silence_status(time_frame, np_freqs):
    """Determine if there is silence at the given time frame."""
    # Silence:
    #   1. The amplitude at every frequency is below a defined threshold.
    for i, amp in enumerate(time_frame['amplitudes']):
        if np_freqs[i] < VOICE_MAX_FREQ:
            amp_min = VOICE_BASE_AMP
        else:
            amp_min = ASPIR_BASE_AMP
        if amp > amp_min:
            time_frame['silence'] = False
            return time_frame
    time_frame['silence'] = True
    return time_frame

def get_vocalization_status(time_frame, np_freqs):
    """Determine if there is vocalization at the given time frame."""
    # "Vocalization" means "sufficient amplitude in the F1-F3 frequency range".
    #   This range is about 100 Hz to 2500 Hz for F1-F2
    #   But maybe it's best to only consider F1, between 100 Hz and 800-1000 Hz.
    for i, freq in enumerate(np_freqs):
        if freq > VOICE_MIN_FREQ and freq < VOICE_MAX_FREQ:
            if time_frame['amplitudes'][i] > VOICE_BASE_AMP:
                time_frame['vocalization'] = True
                return time_frame
            else:
                time_frame['vocalization'] = False
    return time_frame

def get_aspiration_status(time_frame, np_freqs):
    """Determine if there is aspiration at the given time frame."""
    # "Aspiration" means "sufficient amplitude in the >2500 Hz frequency range
    #   for a sufficient number of frequencies".
    freq_ct, aspir_ct = 0, 0
    for i, freq in enumerate(np_freqs):
        if freq > ASPIR_MIN_FREQ:
            freq_ct += 1
            if time_frame['amplitudes'][i] > ASPIR_BASE_AMP:
                aspir_ct += 1
    if aspir_ct / freq_ct > ASPIR_FREQ_RATE:
        time_frame['aspiration'] = True
    else:
        time_frame['aspiration'] = False
    return time_frame

def get_formants(time_frame, np_freqs):
    """Collect up to two formant frequencies found in the given time frame."""
    # Find top two frequencies by highest amplitude below VOICE_MAX_FREQ.
    time_frame['formants'] = []
    # List all amplitudes in vocalization range.
    amps = {}
    for i, freq in enumerate(np_freqs):
        if freq > VOICE_MIN_FREQ and freq < VOICE_MAX_FREQ:
            amps[i] = time_frame['amplitudes'][i]
    # Find peak amplitudes.
    peaks = {}
    last_amp = 0
    for i, amp in amps.items():
        if last_amp > VOICE_BASE_AMP and amp < last_amp and not peaks.get(i-2):
            peaks[i-1] = last_amp
        last_amp = amp
    for i, amp in peaks.items():
        time_frame['formants'].append(round(np_freqs[i]))
    return time_frame

def get_time_frames(np_spectrum, np_freqs, np_times):
    # Organize data into dictionary.
    time_frames = {t: {'index': i} for i, t in enumerate(np_times)}
    for t, time_frame in time_frames.items():
        # Add amplitudes to dictionary.
        time_frame = get_amplitudes(time_frame, np_spectrum)
        # Add silence status to dictionary.
        time_frame = get_silence_status(time_frame, np_freqs)
        # Add vocalization status to dictionary.
        time_frame = get_vocalization_status(time_frame, np_freqs)
        # Add aspiration status.
        time_frame = get_aspiration_status(time_frame, np_freqs)
        # Find formants.
        time_frame = get_formants(time_frame, np_freqs)
        # Add accumulated data to dictionary.
        time_frames[t] = time_frame
    return time_frames

def get_phoneme_starts(phonemes, time_frames):
    """Note time frames where sound begins after silence."""
    # TODO: Consider that not all phonemes are separated by silence.
    # Separators:
    #   - silence
    #   - abrupt change in formants
    start = 0
    end = 1
    phoneme_ct = 0
    faux_silence_max = 0.005 # seconds; 
    # Dict of time frame indexes and corresponding times.
    times = {tf['index']: t for t, tf in time_frames.items()}
    tot_frames = len(times)
    for t, time_frame in time_frames.items():
        t = round(t, 4)
        i = time_frame['index']
        # Check if phoneme has already begun and if current time frame has silence.
        if time_frame['silence']:
            if i == 0:
                print(i, t, "silence has just started")
                silence_start = 0
                continue
            if not time_frames[times[i-1]]['silence']:
                print(i, t, "silence started; ", end='')
                silence_start = t
                if time_frames.get(times[i+1]) and not time_frames[times[i+1]]['silence']:
                    # This frame is a one-off.
                    print("single frame of silence; ignoring")
                    continue
            silence_dur = round(t - silence_start, 4)
            if start:
                if silence_dur > faux_silence_max:
                    # TODO: if start is too close to previous end, then assume it is
                    #   actually the same phoneme.
                    # End time was earlier time frame's time.
                    silence_start = round(t - silence_dur, 4)
                    end = round(t - silence_dur, 4)
                    # Skip single frame of sound.
                    #print(start, end)
                    if start == end:
                        print(i, start, "single frame of sound; resetting start time")
                        start = 0
                        #phoneme_ct -= 1
                        continue
                    print("(", end, "end phoneme )")
                    print(i, t, "silence between phonemes")
                    phoneme_ct += 1
                    phonemes[phoneme_ct] = {'start': start}
                    phonemes[phoneme_ct]['end'] = end
                    start = 0
                else:
                    print(i, "not enough silence: ", silence_dur)
            elif t == times[len(times) - 1]:
                print(i, t, "silence in last frame")
            else:
                print(i) # silence between phonemes
        elif not time_frame['silence']:
            # - First frame handling.
            if i == 0:
                if not start:
                    start = t
                    print(i, t, 'start phoneme')
            elif time_frames[times[i-1]]['silence']:
                if end and not start:
                    start = t
                    print(i, t, 'start phoneme')
                else:
                    print(i, t, "start:", start, "end:", end)
            # - Last frame handling.
            elif t == round(times[len(times) - 1], 4):
                print(i, t, 'end phoneme')
                end = t
                phoneme_ct += 1
                phonemes[phoneme_ct] = {'start': start}
                phonemes[phoneme_ct]['end'] = end
                start = 0
            else:
                print(i, '-') # ongoing phoneme

    return phonemes

def get_phonemes(time_frames):
    phonemes = get_phoneme_starts({}, time_frames)
    return phonemes


# Read arguments; set global variables.
VOICE_MIN_FREQ = 500    # should be more like 200 according to vowel quad.; needs testing
VOICE_MAX_FREQ = 1000   # ref: vowel quadrilateral
VOICE_BASE_AMP = 20000  # empirical number based on testing. What unit is it?!
ASPIR_MIN_FREQ = 2500   # empirical
ASPIR_BASE_AMP = 100    # empirical
ASPIR_FREQ_RATE = 0.1   # empirical; rate of audible vs inaudible frequencies in aspiration range

if len(sys.argv) > 1:
    infile_str = sys.argv[1]

    # Convert to WAV if necessary.
    input_file = get_full_path_obj(infile_str)
    if input_file.suffix != '.wav':
        input_file = convert_to_wav(input_file)

    # Retrieve file data.
    file_info, byte_frames = get_wav_info(input_file)

startfr = None
endfr = None
if len(sys.argv) > 2:
    endsec = float(sys.argv[-1])
    endfr = int(endsec * file_info.framerate) # * file_info.sampwidth)
if len(sys.argv) == 4:
    startsec = float(sys.argv[2])
    startfr = int(startsec * file_info.framerate) # * file_info.sampwidth)

# Convert byte_frames to np_frames, crop according to start and end args.
np_frames = np.frombuffer(byte_frames, dtype='int16')
np_frames = np_frames[startfr:endfr]

# Generate illustrative plots; return spectrum.
np_spectrum, np_freqs, np_times = generate_plots(input_file, np_frames, file_info.framerate)
# Normalize specturm by applying filters.
np_spectrum, np_freqs = normalize_spectrum(np_spectrum, np_freqs, np_times)
# Organize time frame data into dictionary.
time_frames = get_time_frames(np_spectrum, np_freqs, np_times)

phonemes = get_phonemes(time_frames)
print(phonemes)

#print_terminal_spectrogram(np_spectrum, np_freqs, np_times, time_frames)
# Output descriptive properties of spectrum.
#show_spectrum_properties(np_spectrum, np_freqs, np_times)
