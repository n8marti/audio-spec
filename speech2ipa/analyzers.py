"""Functions that analyze the audio data."""

import numpy as np

from matplotlib import pyplot as plt

from speech2ipa import utils


# Read arguments; set global variables.
VOICE_MIN_FREQ = 200    # see vowel quadrilateral
VOICE_MAX_FREQ = 3000   # see vowel quadrilateral

# Note: A "peak amplitude range" is a measure of how consistent or steady the
#   amplitudes are across all frequencies at a given moment of time.
#   It is found in this way:
#       TODO: rewrite calculation description.
AMPS_AVG_MIN = 300              # arbitrary; to distinguish turbulence from silence
TURB_AMPS_DEV_MIN = 3000        # arbitrary; to distinguish turbulence from vocalization
TURB_PEAKS_DEV_MIN = 4000       # arbitrary; to distinguish turbulence from vocalization (redundant)
VOICE_PEAK_AMP_RANGE_MIN = 7500     # arbitrary; 2000 seems a little overbroad


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
def get_time_frames(np_spectrum, np_freqs, np_times, startsec, endsec):
    # Organize data into dictionary.
    time_frames = {}
    max_amp = max(np_spectrum.flat)
    for i, t in enumerate(np_times):
        if startsec <= t <= endsec:
            time_frames[t] = {'index': i}
    #time_frames = {t: {'index': i} for i, t in enumerate(np_times)}
    for t, time_frame in time_frames.items():
        # Add amplitudes to dictionary.
        time_frame = get_amplitudes(time_frame, np_spectrum, max_amp)
        # Add silence status to dictionary.
        time_frame = get_silence_status(time_frame, np_freqs)
        # Add vocalization status to dictionary.
        time_frame = get_vocalization_status(time_frame, np_freqs)
        # Add turbulence status.
        time_frame = get_turbulence_status(time_frame, np_freqs)
        # Find formants.
        time_frame = get_formants(time_frame, np_freqs)
        # Add accumulated data to dictionary.
        time_frames[t] = time_frame
    return time_frames

def get_amplitudes(time_frame, np_spectrum, max_amp):
    """Add the amplitude at each frequency to the given time frame."""
    # Since these values are inconsistent, they are normalized to a max of 1,000,000.
    time_frame['amplitudes'] = [row[time_frame['index']] / max_amp * 1_000_000 for row in np_spectrum]
    return time_frame

def get_silence_status(time_frame, np_freqs):
    """Determine if there is silence at the given time frame."""
    # Silence:
    #   TODO: rewrite description of calculation.
    amps_list = [a for a in time_frame['amplitudes']]
    amps_range, amps_sum, amps_avg, amps_std_dev = utils.get_list_stats(amps_list)
    if amps_avg < AMPS_AVG_MIN and amps_std_dev < TURB_AMPS_DEV_MIN:
        time_frame['silence'] = True
    else:
        time_frame['silence'] = False
    return time_frame

def get_vocalization_status(time_frame, np_freqs):
    """Determine if there is vocalization at the given time frame."""
    # "Vocalization" means "sufficient amplitude in the F1-F3 frequency range".
    #valid_amps = []
    #for i, freq in enumerate(np_freqs):
    #    if freq > VOICE_MIN_FREQ and freq < VOICE_MAX_FREQ:
    #        valid_amps.append(time_frame['amplitudes'][i])
    #peak_amps_range = utils.get_peak_amps_range(valid_amps)
    #if peak_amps_range > VOICE_PEAK_AMP_RANGE_MIN:
    amps_list = [a for a in time_frame['amplitudes']]
    amps_range, amps_sum, amps_avg, amps_std_dev = utils.get_list_stats(amps_list)
    if amps_avg < AMPS_AVG_MIN and amps_std_dev > TURB_AMPS_DEV_MIN:
        time_frame['vocalization'] = True
    else:
        time_frame['vocalization'] = False
    return time_frame

def get_turbulence_status(time_frame, np_freqs):
    """Determine if there is turbulence at the given time frame."""
    # https://home.cc.umanitoba.ca/~krussll/phonetics/acoustic/spectrogram-sounds.html

    # "Turbulence" means "sufficient and consistent amplitude in the >2500 Hz
    #   frequency range for a sufficient number of frequencies".
    #valid_amps = {}
    #TURB_MIN_FREQ = 5500   # arbitrary; turbulence can start at any frequency.
    #for i, freq in enumerate(np_freqs):
    #    if freq > TURB_MIN_FREQ:
    #        valid_amps[i] = time_frame['amplitudes'][i]

    # "Turbulence" means "sufficient amplitude with std. dev. of amplitudes < 3000".
    valid_amps = {i: a for i, a in enumerate(time_frame['amplitudes'])}
    amps_list = [a for a in valid_amps.values()]
    amps_range, amps_sum, amps_avg, amps_std_dev = utils.get_list_stats(amps_list)
    M_sum = 0
    for i, a in valid_amps.items():
        M_sum += np_freqs[i] * a # distance measured from bottom, 0 Hz
    amps_Fmid = M_sum / amps_sum
    print(f"{time_frame['index']}:\tamps avg: {round(amps_avg)}\tamps Fmid: {round(amps_Fmid)}\tamps stdev: {round(amps_std_dev)}")
    if amps_avg > AMPS_AVG_MIN and amps_std_dev < TURB_AMPS_DEV_MIN:
        time_frame['turbulence'] = True
    else:
        time_frame['turbulence'] = False
    return time_frame

def get_formants(time_frame, np_freqs):
    """Collect all lower formant frequencies found in the given time frame."""
    time_frame['formants'] = []
    valid_amps = []
    for i, freq in enumerate(np_freqs):
        if VOICE_MIN_FREQ < freq < VOICE_MAX_FREQ:
            amp = time_frame['amplitudes'][i]
            amp_min = utils.get_min_amp(freq)
            print(amp_min, amp)
            if amp > amp_min:
                valid_amps.append(amp)
    peaks = utils.get_peak_amps(valid_amps)
    # Get corresponding frequency of each peak amplitude.
    for i, freq in enumerate(np_freqs):
        if time_frame['amplitudes'][i] in peaks:
            time_frame['formants'].append(round(freq))
    return time_frame

def get_sample_properties(time_frames):
    props = {}
    props['duration'] = {'value': round(max(time_frames.keys()), 3), 'unit': 's'}
    return props

# ------------------------------------------------------------------------------
# Analyze data to find separations between phonemes in the audio track.
# ------------------------------------------------------------------------------
def get_phonemes(time_frames):
    phonemes = {}
    frame_total = len(time_frames)
    start_ct = 0
    ch_sil_prev = False
    ch_voc_prev = False
    ch_tur_prev = False
    #print(f"Time\tdSil\tdVoc\tdTur")
    indexes = [d['index'] for d in time_frames.values()]
    for t, data in time_frames.items():
        if data['index'] == min(indexes):
            # First frame.
            pass
        else:
            # Normal processing.
            ch_sil = is_changed('silence', time_frames, t)
            ch_voc = is_changed('vocalization', time_frames, t)
            ch_tur = is_changed('turbulence', time_frames, t)
            if (ch_sil and ch_sil_prev) or (ch_voc and ch_voc_prev) or (ch_tur and ch_tur_prev):
                # Ignore rapidly-changing properties.
                ch_sil_prev = ch_sil
                ch_voc_prev = ch_voc
                ch_tur_prev = ch_tur
                continue
            #print(f"{round(t, 3)}\t{ch_sil}\t{ch_voc}\t{ch_tur}")
            if not data['silence'] and (ch_sil or ch_voc or ch_tur):
                # There is no longer silence, but there might not yet be any
                #   vocalization or turbulence.
                start_ct += 1
                #print(f"start at {t}")
                phonemes[start_ct] = {}
            ch_sil_prev = ch_sil
            ch_voc_prev = ch_voc
            ch_tur_prev = ch_tur
    print(len(phonemes))
    return phonemes

def is_changed(property, time_frames, t):
    i = time_frames[t]['index']
    for time, data in time_frames.items():
        if data['index'] == i - 1:
            t_prev = time
            break
    prop_prev = time_frames[t_prev][property]
    if time_frames[t][property] == prop_prev:
        is_changed = False
    else:
        is_changed = True
    return is_changed

def formants_is_changed(time_frames, t):
    pass

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
