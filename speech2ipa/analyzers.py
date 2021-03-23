"""Functions that analyze the audio data."""

import math

from matplotlib import pyplot as plt

from speech2ipa import utils


# Read arguments; set global variables.
VOICE_MIN_FREQ = 200    # see vowel quadrilateral
VOICE_MAX_FREQ = 3000   # see vowel quadrilateral
ASPIR_MIN_FREQ = 2500   # arbitrary; aspiration can start a any frequency.
# Note: A "peak amplitude range" is a measure of how consistent or steady the
#   amplitudes are across all frequencies at a given moment of time.
#   It is found in this way:
#       At a given point in time all the amplitudes (one from each frequency) are
#       listed. Relative maximums (i.e. "peaks") are then found in this list. The
#       range, then, is the difference between the higest peak amplitude and the
#       lowest peak amplitude.
VOICE_PEAK_AMP_RANGE_MIN = 5000     # arbitrary; 2000 seems a little overbroad
ASPIR_PEAK_AMP_RANGE_MIN = 100      # arbitrary
ASPIR_PEAK_AMP_RANGE_MAX = 2000     # arbitrary
SILENCE_PEAK_AMP_RANGE_MAX = 500    # arbitrary

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

    # If NFFT is too high, then there the horizontal (frequency) resolution is
    #   too fine, and there are multiple bands for each formant. However, if
    #   NFFT is too low, then the whole image is rather blurry and even the
    #   formants are not well differentiated (i.e. at the default vaules for NFFT
    #   and noverlap). noverlap that is half of NFFT seems to minimize background
    #   noise, as well.
    noverlap = 128          # default: 128; other: 256
    NFFT = 256              # default: 256; other: 512

    # Create the plot.
    spectrum, frequencies, times, img = plt.specgram(
        np_frames,
        Fs=frame_rate,
        cmap='gnuplot',
        noverlap=noverlap,
        NFFT=NFFT,
    )
    return spectrum, frequencies, times, img

# ------------------------------------------------------------------------------
# Analyze data related to each time frame in the audio track.
# ------------------------------------------------------------------------------
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
    #   The amplitude at every frequency is below a defined threshold.
    #   The peak amplitude range is below that of aspiration.
    #       NB: Some kinds of white noise would also probably qualify here.
    valid_amps = []
    for i, freq in enumerate(np_freqs):
        if freq > VOICE_MIN_FREQ:
            valid_amps.append(time_frame['amplitudes'][i])
    peak_amps_range = utils.get_peak_amps_range(valid_amps)
    if peak_amps_range < SILENCE_PEAK_AMP_RANGE_MAX:
        time_frame['silence'] = True
    else:
        time_frame['silence'] = False
    return time_frame

def get_vocalization_status(time_frame, np_freqs):
    """Determine if there is vocalization at the given time frame."""
    # "Vocalization" means "sufficient amplitude in the F1-F3 frequency range".
    valid_amps = []
    for i, freq in enumerate(np_freqs):
        if freq > VOICE_MIN_FREQ and freq < VOICE_MAX_FREQ:
            valid_amps.append(time_frame['amplitudes'][i])
    peak_amps_range = utils.get_peak_amps_range(valid_amps)
    if peak_amps_range > VOICE_PEAK_AMP_RANGE_MIN:
        time_frame['vocalization'] = True
    else:
        time_frame['vocalization'] = False
    return time_frame

def get_aspiration_status(time_frame, np_freqs):
    """Determine if there is aspiration at the given time frame."""
    # "Aspiration" means "sufficient and consistent amplitude in the >2500 Hz
    #   frequency range for a sufficient number of frequencies".
    valid_amps = []
    for i, freq in enumerate(np_freqs):
        if freq > ASPIR_MIN_FREQ:
            valid_amps.append(time_frame['amplitudes'][i])
    peak_amps_range = utils.get_peak_amps_range(valid_amps)
    if ASPIR_PEAK_AMP_RANGE_MIN < peak_amps_range < ASPIR_PEAK_AMP_RANGE_MAX:
        time_frame['aspiration'] = True
    else:
        time_frame['aspiration'] = False
    return time_frame

def get_formants(time_frame, np_freqs):
    """Collect up to two formant frequencies found in the given time frame."""
    '''
    # Find top two frequencies by highest amplitude below VOICE_MAX_FREQ.
    time_frame['formants'] = []
    # List all amplitudes in vocalization range.
    amps = {}
    for i, freq in enumerate(np_freqs):
        if freq > VOICE_MIN_FREQ and freq < VOICE_MAX_FREQ:
            amps[i] = time_frame['amplitudes'][i]
        else:
            amps[i] = None
    # Find peak amplitudes.
    peaks = {}
    last_amp = 0
    for i, amp in amps.items():
        if amp and last_amp and not peaks.get(i-2) \
            and last_amp > utils.get_min_amp(np_freqs[i]) and amp < last_amp:
            peaks[i-1] = last_amp
        last_amp = amp
    for i, amp in peaks.items():
        time_frame['formants'].append(round(np_freqs[i]))
    '''
    time_frame['formants'] = []
    valid_amps = []
    for i, freq in enumerate(np_freqs):
        if VOICE_MIN_FREQ < freq < VOICE_MAX_FREQ:
            valid_amps.append(time_frame['amplitudes'][i])
    peaks = utils.get_peak_amps(valid_amps)
    #print(peaks)
    # To get formants, choose only 3 highest peaks.
    #top_amps = []
    #while len(top_amps) < 3 and len(peaks) > 0:
    #    top_amps.append(max(peaks))
    #    peaks.remove(max(peaks))
    top_amps = peaks.copy()
    # Get corresponding frequency of each top3 amplitude.
    for i, freq in enumerate(np_freqs):
        if time_frame['amplitudes'][i] in top_amps:
            #print(f"{freq}\t{time_frame['amplitudes'][i]}")
            time_frame['formants'].append(round(freq))
    return time_frame

# ------------------------------------------------------------------------------
# Analyze data find separations between phonemes in the audio track.
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# Analyze data to describe or identify each phoneme in the audio track.
# ------------------------------------------------------------------------------
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
