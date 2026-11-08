# Evaluation protocols

A scorer name alone is not a reproducible experimental condition. Record the dataset split, reference construction, input hashes, normalization, assignment rules, time policy, backend/model identity, coverage and aggregation.

## Text and speaker-attributed ASR

The preserved `speech-eval-mt-v1.0` profile uses MeetEval 0.4.3 and kaldialign 0.12.0. It applies NFKC/casefold, punctuation boundaries, preserved internal apostrophes, and a documented initialism rule. Repetitions, fillers and written numbers are retained. Numbers are not verbalized. CER uses normalized Unicode letters/marks/numbers without spaces; Chinese words are not implicitly segmented.

- **WER/CER:** errors divided by reference units. Empty references have an undefined per-item rate; insertions remain in a corpus numerator.
- **cpWER/cpCER:** one global speaker permutation per recording. Splitting a recording changes the optimization problem.
- **tcpWER/tcpCER:** additionally constrain temporal alignment. This profile uses reference `character_based` and hypothesis `character_based_points` pseudo-word timing, with segment ordering. A collar of 5 seconds is a local default, not a universal standard; compare explicit 2/5-second settings when useful.
- **ORC/MIMO:** use different utterance/channel assignment constraints. They are not interchangeable substitutes for speaker-attributed cpWER.
- **greedy DI variants:** the algorithm name explicitly identifies a greedy approximation.
- **TS-ASR:** select the target according to the task definition before scoring. Do not minimize errors over candidate speakers using the reference.

Interpolated sentence timing does not equal manually annotated word timing. Inspect timing validity and reference coverage before reporting a time-constrained score. A difference between cpWER and tcpWER is not an independent, isolated timing error rate.

## Diarization and speech activity

DER/JER/VAD use pyannote.metrics with an explicit UEM, collar and overlap policy. `reference_is_speech_activity=True` confirms that reference spans really describe activity. Sentence spans in an ASR transcript are not automatically such annotations.

DER accumulates confusion, missed detection and false-alarm durations over reference speech time. JER accumulates per-reference-speaker errors over reference speaker count. VAD scores accumulate the corresponding time components. Speaker-count error is a separate diagnostic: the correct number of clusters does not establish correct assignments or boundaries.

## Waveform comparisons

PESQ, STOI/ESTOI and SI-SDR require equal-length finite mono signals with an explicit sample rate. The library does not silently crop, optimize delay, fit gain or select a better reference. PESQ resamples with soxr HQ to 16 kHz WB or 8 kHz NB. STOI retains upstream internal processing. SI-SDR uses zero-mean signals; SI-SDRi subtracts a mixture baseline measured against the same clean reference.

BSS SDR/SIR/SAR use the upstream filter/permutation implementation with explicit parameters. They require a complete multi-source reference matrix and estimates. An infinite score from perfect reconstruction is not silently clamped to an arbitrary dB ceiling.

## Model-based measures

The model checkpoint is part of the metric definition. Record source revision, weight hash, inference configuration, sample-rate handling and reference selection. Nonmatching-reference quality assessment differs from aligned-reference fidelity assessment.

- SCOREQ: natural/synthetic × nr/ref; NR predicts MOS, REF measures distance. Synthetic REF uses the nonmatching-reference profile.
- NISQA: all five outputs are quality ratings, including noisiness quality; higher NOI does not mean more noise energy.
- Audiobox PC: production complexity is descriptive, not a quality objective.
- SpeechBERTScore: frame matching in learned representations, not a timestamp error.
- IPA similarity: the retained definition computes character edits on decoded IPA after removing spaces; it is not phone-token PER and may be negative.
- Whisper dWER: compares two ASR-derived texts. Whisper WER uses ground-truth text. The validated profile uses English normalization, deterministic beam search and <=30-second clips.

## Dataset summaries

WER-like measures use micro aggregation; waveform quality uses utterance macro averaging; rating correlations operate on the full paired array. Do not pool different corpora, languages/token units, collars, reference definitions or model fingerprints without defining a defensible protocol.

Report expected/scored counts and failures. A valid-subset score is not the full-test score. Model output ratings are predictions and should not be relabeled as subjective listening-study MOS.
