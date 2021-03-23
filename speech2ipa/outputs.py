"""Functions used to generate various outputs from the given WAV file."""

import numpy as np
import matplotlib.ticker as ticker
import wave

from matplotlib import pyplot
from scipy.fft import irfft, rfft, rfftfreq

from speech2ipa import utils

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

    """
    ### This doesn't result in a "narrow" enough bandwidth; i.e. the frequencies
    # Set NFFT so that there are ~100 columns per second of audio.
    #       have too much resolution and each formant is split into multiple
    #       bands.
    columns_per_sec = 100   # desired horizontal resolution
    noverlap = 500          # default: 128; correlates with vertical resolution
    # matplotlib says that an NFFT that is a power of 2 is most efficient,
    #   but how would I round the calculation to the nearest power of 2?
    NFFT = int(frame_rate / columns_per_sec + noverlap) # NFFT = 941
    """
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

def print_spectrum_properties(np_spectrum, np_freqs, np_times):
    """Print out insightful properties of the normalized spectrum data."""
    # Duration (s)
    # Frequency range (max 8 kHz)
    duration = round(np_times[-1], 2)
    max_amp_raw = max(np_spectrum.flat)
    min_amp_raw = min(np_spectrum.flat)

    print(f"Duration: {duration} s")

def print_frame_data(time_frames, startsec):
    print(f"Time\tSilence\tVocal.\tAspir.\tFormants")
    for t, data in time_frames.items():
        print(f"{round(t + startsec, 3)}\t{data['silence']}\t{data['vocalization']}\t{data['aspiration']}\t{data['formants']}")

def print_terminal_spectrogram(np_spectrum, np_freqs, np_times, time_frames=False):
    """Print out a basic spectrogram in the terminal for debugging."""
    for ri, r in enumerate(np_spectrum[::-1]):
        # Print frequency scale item.
        freq = np_freqs[len(np_freqs) - ri - 1]
        if ri % 2 == 0:
            print(f"{int(freq / 1000)}K ", end='')
        else:
            print('   ', end='')
        # Print frequency rows.
        for a in r:
            #min_amp = utils.get_min_amp(freq)
            min_amp = 10
            if a < min_amp:
                print('   ', end='')
            elif a < 100 * min_amp:
                print('-  ', end='')
            elif a < 10000 * min_amp:
                print('*  ', end='')
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
