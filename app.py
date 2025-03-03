#!/usr/bin/env python3
"""Read and parse speech info from audio files."""

import sys

from pathlib import Path

from speech2ipa import analyzers, filters, outputs, utils


if __name__ == '__main__':

    if len(sys.argv) > 1:
        infile_str = sys.argv[1]

        # Convert to WAV if necessary.
        input_file = utils.get_input_path_obj(infile_str)
        if input_file.suffix != '.wav':
            input_file = utils.convert_to_wav(input_file)

        # Retrieve file data.
        file_info, byte_frames = utils.get_wav_info(input_file)

    startfr = None
    startsec = 0
    endfr = None
    endsec = None
    if len(sys.argv) > 2:
        endsec = float(sys.argv[-1])
        endfr = int(endsec * file_info.framerate) # * file_info.sampwidth)
    if len(sys.argv) == 4:
        startsec = float(sys.argv[2])
        startfr = int(startsec * file_info.framerate) # * file_info.sampwidth)

    # Convert byte_frames to np_frames, crop according to start and end args.
    np_frames = utils.convert_to_np_frames(byte_frames)

    # Generate illustrative plots; return spectrum.
    #np_spectrum, np_freqs, np_times = outputs.generate_plots(input_file, np_frames, file_info.framerate)
    np_spectrum, np_freqs, np_times, img = analyzers.get_spectrogram_data(file_info.framerate, np_frames)
    # Normalize specturm by applying filters.
    np_spectrum, np_freqs = filters.normalize_spectrum(np_spectrum, np_freqs, np_times)
    # Organize time frame data into dictionary.
    time_frames = analyzers.get_time_frames(np_spectrum, np_freqs, np_times, startsec, endsec)

    #outputs.print_sample_properties(analyzers.get_sample_properties(time_frames))
    #outputs.print_terminal_spectrogram(np_spectrum, np_freqs, np_times, time_frames)
    analyzers.get_phonemes(time_frames)
    #outputs.print_frequencies(np_freqs)
    #outputs.print_amplitudes(time_frames)
    print()
    outputs.print_frame_data(time_frames)

    exit()
