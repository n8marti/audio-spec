"""Functions that analyze the audio data."""

from matplotlib import pyplot as plt


# Read arguments; set global variables.
VOICE_MIN_FREQ = 500    # should be more like 200 according to vowel quad.; needs testing
VOICE_MAX_FREQ = 1000   # ref: vowel quadrilateral
VOICE_BASE_AMP = 20000  # empirical number based on testing. What unit is it?!
ASPIR_MIN_FREQ = 2500   # empirical
ASPIR_BASE_AMP = 100    # empirical
ASPIR_FREQ_RATE = 0.1   # empirical; rate of audible vs inaudible frequencies in aspiration range

def get_spectrogram_data(frame_rate, np_frames):
    """Convert audio frames to spectrogram data array."""
    # Set format details for plot.
    #fig = plt.figure(num=None, figsize=(12, 7.5), dpi=300)
    #ax = fig.add_subplot(111)
    #ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    #ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    #ax.yaxis.set_major_locator(ticker.MultipleLocator(2000))
    #ax.yaxis.set_minor_locator(ticker.MultipleLocator(500))
    #ax.tick_params(axis='both', direction='inout')
    #plt.title(f"Spectrogram of:\n{input_file}")
    plt.title(f"Spectrogram")
    plt.xlabel('Time (seconds)')
    plt.ylabel('Frequency (Hz)')

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
    spectrum, frequencies, times, img = plt.specgram(
        np_frames,
        Fs=frame_rate,
        cmap='gnuplot',
        noverlap=noverlap,
        NFFT=NFFT,
    )
    return spectrum, frequencies, times, img

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
