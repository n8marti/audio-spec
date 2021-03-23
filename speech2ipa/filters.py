"""Functions that filter the audio data."""

import numpy as np


def normalize_spectrum(np_spectrum, np_freqs, np_times):
    """Normalize specturm by applying desired filters."""
    # Trim out high frequencies (> 8 kHz).
    np_spectrum, np_freqs = cut_high_freqs(np_spectrum, np_freqs)
    # Trim out background white noise.
    #np_spectrum = subtract_bg_noise(np_spectrum, np_freqs, np_times)

    return np_spectrum, np_freqs

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
