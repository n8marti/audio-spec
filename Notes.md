# Notes

## Acoustic properties of an audio recording
- duration [s]
- register (gender): low (adult male) / medium (adult female) / high (child)
- pace [vowels/sec]?

## Acoustic properties of a phoneme
- [ ] ID vowel vs consonant
- [ ] voicing/aspiration (voiced: V is True; aspir.: V is False, S is False)
- [x] formant frequencies: F1 > pharyngeal cavity, F2 > front cavity, [Hz]
  - F3 > vocal folds, but not needed for distinguishing between vowels
- [ ] effect of different stops (consonants) on adjacent vowels
- [ ] length/duration [s]
  - [ ] start time [s]
  - [ ] end time [s]

## Separators between phonemes
- [ ] change silence status
- [ ] change in aspiration status
- [ ] change in vocalization status
- [ ] change in formant list (dipthongs), but harder to get good accuracy

## Acoustic properties of a time slice of audio
- [x] silence: True / False
- [x] vocalization: True / False
- [x] turbulence: True / False
- [x] formants: F1, F2 [Hz] (consider F3)

# General research

https://linguistics.stackexchange.com/questions/3783/convert-audio-recording-of-word-to-ipa-representation#3800
The gist of the complexity of the problem:
- IPA designations are not exactly standardized.
- There seems to be no other standarized system that matches acoustic speech properties to generic written characters.

http://www.linguisticsnetwork.com/the-basics-about-acoustic-phonetics/
>The majority of human sounds falls between 250-4000 Hz
>
>Formants are the crest, or spectral peaks of a sound wave. Formants occur at around 1,000 Hz and correspond to a measurement of resonance produced in the vocal tract during phonation. The formant with the lowest frequency is referred to as the F1, the second F2, the third F3, etc.

https://linguistics.stackexchange.com/questions/23060/where-to-download-wav-mp3-files-for-each-of-the-ipa-phoneme
Discussion on combining IPA phoneme recordings into words. Especially, this:
>You can get a steady-state recording of "ɪ" (the snippet of "ɪ" on that page is 458 msc. long, which is abnormally long for speech). But "t" and "p" simply involve closing the lips or raising the tongue, and there is no actual sound during their production, so all you have is silence (the ability to discern "p" versus "t" comes from the formant transition effect that these articulations have on adjacent sonorants). This, "tick, tip, tit, pit, kit..." would all sound the same using this technique, namely [ɪ].

## The Acoustic Properties of Vowels

https://my.ilstu.edu/~jsawyer/consonantsvowels3/consonantsvowels23.html

The distance between the [vertical] lines [on a spectrogram] for adult males represent approximately 1/100th of a second, and for adult females, 1/200th of a second.

https://my.ilstu.edu/~jsawyer/consonantsvowels3/consonantsvowels24.html

### Formants of /i/, /a/, and /u/

Formant | i | a | u
-- | --: | --: | --:
F1 | 300 | 800 | 300
F2 | 2500 | 1000 | 900
F3 | 3010 | 2500 | 2500

F1 is the lowest of all the vowels for the sound /i/. The constriction at the point of maximum pressure tends to raise F2 and F3. As you know, a neutrally shaped male adult vocal tract would have resonant frequencies of 500, 1,500, and 2,500 Hz. We can see that when /i/ is produced, F1 = 270 Hz, F2= 2290 Hz, and F3 = 3010 Hz.

### Vowel Quadrilateral
![](./vowel.quadrilateral.jpg)

## Properties of speech sound features

http://www.linguisticsnetwork.com/features/

### Consonants
For stops, fricatives, and affricates:
- voicing/aspiration
- place of articulation
- manner of articulation

For nasals, liquids, and glides:
- place of articulation
- manner of articulation
- Voicing is not mentioned since these phonemes are always voiced.

### Vowels
- height
- part of the tongue
- tense/lax (ATR/RTR)
- roundness
