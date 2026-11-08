# Metric catalog

**84 canonical variants and 5 migration aliases.** Counts include distinct modes and output heads; they are not counts of original algorithms. This catalog is generated from the shipped registry.

See [API inputs](API.md), [model configuration](MODELS.md), [protocols](PROTOCOLS.md) and the [validation matrix](../validation/summary.json). Original interfaces retain their v0.2 evidence. New profiles are evaluated separately in the [v0.4 report](../validation/expansion-v0.4.json).

| Dimension | Canonical variants |
|---|---:|
| `recognition` | 16 |
| `speaker_structure` | 3 |
| `perceptual_quality` | 30 |
| `intelligibility` | 2 |
| `signal_fidelity` | 9 |
| `audio_aesthetics` | 4 |
| `speaker_identity` | 4 |
| `echo_attenuation` | 1 |
| `content_similarity` | 8 |
| `rating_agreement` | 3 |
| `speech_activity` | 4 |

## `wer`

Word error rate

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | asr, ts_asr, tts, codec |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `cer`

Character error rate

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | asr, ts_asr, tts, codec |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `ts_wer`

Target-speaker word error rate

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | asr, ts_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `ts_cer`

Target-speaker character error rate

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | asr, ts_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `cpwer`

Concatenated minimum-permutation WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | mt_asr, meeting |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `cpcer`

Concatenated minimum-permutation CER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | mt_asr, meeting |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `tcpwer`

Time-constrained minimum-permutation WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | mt_asr, meeting |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `tcpcer`

Time-constrained minimum-permutation CER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | mt_asr, meeting |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `der`

Diarization error rate

| Property | Contract |
|---|---|
| Measurement | `speaker_structure` |
| Reference | `speaker_annotation` |
| Output | `percent`; `lower_is_better` |
| Task tags | diarization, meeting |
| Source | [Upstream implementation](https://github.com/pyannote/pyannote-metrics) |

DER/JER require genuine activity annotations, explicit UEM, collar and overlap policy. Speaker count is an auxiliary cardinality diagnostic, not a replacement for assignment or timing quality.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `jer`

Jaccard error rate

| Property | Contract |
|---|---|
| Measurement | `speaker_structure` |
| Reference | `speaker_annotation` |
| Output | `percent`; `lower_is_better` |
| Task tags | diarization, meeting |
| Source | [Upstream implementation](https://github.com/pyannote/pyannote-metrics) |

DER/JER require genuine activity annotations, explicit UEM, collar and overlap policy. Speaker count is an auxiliary cardinality diagnostic, not a replacement for assignment or timing quality.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `pesq_wb`

PESQ wideband, 16 kHz

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `aligned_waveform` |
| Output | `backend_score`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec |
| Source | [Upstream implementation](https://github.com/ludlows/PESQ) |

PESQ WB scores at 16 kHz, NB at 8 kHz. Other input rates use soxr HQ; no implicit gain fitting, cropping or delay search. This is not POLQA. Upstream licensing applies.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `pesq_nb`

PESQ narrowband, 8 kHz

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `aligned_waveform` |
| Output | `backend_score`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec |
| Source | [Upstream implementation](https://github.com/ludlows/PESQ) |

PESQ WB scores at 16 kHz, NB at 8 kHz. Other input rates use soxr HQ; no implicit gain fitting, cropping or delay search. This is not POLQA. Upstream licensing applies.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `stoi`

Short-time objective intelligibility

| Property | Contract |
|---|---|
| Measurement | `intelligibility` |
| Reference | `aligned_waveform` |
| Output | `backend_score`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec |
| Source | [Upstream implementation](https://github.com/mpariente/pystoi) |

pystoi 0.4.1; extended=False for STOI and True for ESTOI. Equal-length mono inputs with explicit sample rate; upstream internal 10 kHz processing is preserved. Backend warnings from inadequate signal support are not presented as valid scores.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `estoi`

Extended STOI

| Property | Contract |
|---|---|
| Measurement | `intelligibility` |
| Reference | `aligned_waveform` |
| Output | `backend_score`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec |
| Source | [Upstream implementation](https://github.com/mpariente/pystoi) |

pystoi 0.4.1; extended=False for STOI and True for ESTOI. Equal-length mono inputs with explicit sample rate; upstream internal 10 kHz processing is preserved. Backend warnings from inadequate signal support are not presented as valid scores.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `si_sdr`

Scale-invariant signal-to-distortion ratio

| Property | Contract |
|---|---|
| Measurement | `signal_fidelity` |
| Reference | `aligned_waveform` |
| Output | `dB`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec |
| Source | [Upstream implementation](https://github.com/fakufaku/fast_bss_eval) |

fast-bss-eval upstream implementation. SI-SDR uses zero_mean=True; SI-SDRi subtracts the mixture baseline. BSS metrics use a complete [sources,samples] matrix, default filter_length=512, zero_mean=False and explicit permutation. Infinite/degenerate results are reported rather than clipped.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `si_sdri`

SI-SDR improvement over mixture

| Property | Contract |
|---|---|
| Measurement | `signal_fidelity` |
| Reference | `aligned_waveform` |
| Output | `dB`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec |
| Source | [Upstream implementation](https://github.com/fakufaku/fast_bss_eval) |

fast-bss-eval upstream implementation. SI-SDR uses zero_mean=True; SI-SDRi subtracts the mixture baseline. BSS metrics use a complete [sources,samples] matrix, default filter_length=512, zero_mean=False and explicit permutation. Infinite/degenerate results are reported rather than clipped.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `speaker_count`

Speaker-count absolute error and cardinality diagnostics

| Property | Contract |
|---|---|
| Measurement | `speaker_structure` |
| Reference | `speaker_annotation` |
| Output | `speakers`; `lower_is_better` |
| Task tags | diarization, mt_asr, meeting |
| Source | local explicit cardinality protocol |

DER/JER require genuine activity annotations, explicit UEM, collar and overlap policy. Speaker count is an auxiliary cardinality diagnostic, not a replacement for assignment or timing quality.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `audiobox_aesthetics_ce`

Content Enjoyment

| Property | Contract |
|---|---|
| Measurement | `audio_aesthetics` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/facebookresearch/audiobox-aesthetics) |
| Model family / head | `audiobox_aesthetics` / `CE` |
| Configuration | `checkpoint` |

The four axes share one forward pass: Content Enjoyment, Content Usefulness, Production Complexity and Production Quality. PC is descriptive, not a higher-is-better quality objective. Upstream 16 kHz resampling and valid-duration weighting are preserved.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `audiobox_aesthetics_cu`

Content Usefulness

| Property | Contract |
|---|---|
| Measurement | `audio_aesthetics` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/facebookresearch/audiobox-aesthetics) |
| Model family / head | `audiobox_aesthetics` / `CU` |
| Configuration | `checkpoint` |

The four axes share one forward pass: Content Enjoyment, Content Usefulness, Production Complexity and Production Quality. PC is descriptive, not a higher-is-better quality objective. Upstream 16 kHz resampling and valid-duration weighting are preserved.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `audiobox_aesthetics_pc`

Production Complexity

| Property | Contract |
|---|---|
| Measurement | `audio_aesthetics` |
| Reference | `none` |
| Output | `predicted_rating`; `descriptive` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/facebookresearch/audiobox-aesthetics) |
| Model family / head | `audiobox_aesthetics` / `PC` |
| Configuration | `checkpoint` |

The four axes share one forward pass: Content Enjoyment, Content Usefulness, Production Complexity and Production Quality. PC is descriptive, not a higher-is-better quality objective. Upstream 16 kHz resampling and valid-duration weighting are preserved.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `audiobox_aesthetics_pq`

Production Quality

| Property | Contract |
|---|---|
| Measurement | `audio_aesthetics` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/facebookresearch/audiobox-aesthetics) |
| Model family / head | `audiobox_aesthetics` / `PQ` |
| Configuration | `checkpoint` |

The four axes share one forward pass: Content Enjoyment, Content Usefulness, Production Complexity and Production Quality. PC is descriptive, not a higher-is-better quality objective. Upstream 16 kHz resampling and valid-duration weighting are preserved.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `scoreq_natural_nr`

SCOREQ natural nr

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/alessandroragano/scoreq) |
| Model family / head | `scoreq_natural_nr` / `score` |
| Configuration | `checkpoint`, `reference_kind (REF only)` |

Choose natural/synthetic and nr/ref with the matching checkpoint. NR predicts MOS; REF is Euclidean embedding distance. Declare matching or nonmatching reference for natural REF; this synthetic REF profile requires nonmatching reference. Official preprocessing/predict uses an explicit local ONNX session.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `scoreq_natural_ref`

SCOREQ natural ref

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `nonmatching_waveform`, `matching_waveform` |
| Output | `embedding_distance`; `lower_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/alessandroragano/scoreq) |
| Model family / head | `scoreq_natural_ref` / `score` |
| Configuration | `checkpoint`, `reference_kind (REF only)` |

Choose natural/synthetic and nr/ref with the matching checkpoint. NR predicts MOS; REF is Euclidean embedding distance. Declare matching or nonmatching reference for natural REF; this synthetic REF profile requires nonmatching reference. Official preprocessing/predict uses an explicit local ONNX session.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `scoreq_synthetic_nr`

SCOREQ synthetic nr

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/alessandroragano/scoreq) |
| Model family / head | `scoreq_synthetic_nr` / `score` |
| Configuration | `checkpoint`, `reference_kind (REF only)` |

Choose natural/synthetic and nr/ref with the matching checkpoint. NR predicts MOS; REF is Euclidean embedding distance. Declare matching or nonmatching reference for natural REF; this synthetic REF profile requires nonmatching reference. Official preprocessing/predict uses an explicit local ONNX session.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `scoreq_synthetic_ref`

SCOREQ synthetic ref

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `nonmatching_waveform` |
| Output | `embedding_distance`; `lower_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/alessandroragano/scoreq) |
| Model family / head | `scoreq_synthetic_ref` / `score` |
| Configuration | `checkpoint`, `reference_kind (REF only)` |

Choose natural/synthetic and nr/ref with the matching checkpoint. NR predicts MOS; REF is Euclidean embedding distance. Declare matching or nonmatching reference for natural REF; this synthetic REF profile requires nonmatching reference. Official preprocessing/predict uses an explicit local ONNX session.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_sig`

DNSMOS SIG

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `SIG` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_bak`

DNSMOS BAK

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `BAK` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_ovrl`

DNSMOS OVRL

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `OVRL` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_p808_mos`

DNSMOS P808_MOS

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `P808_MOS` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_sig_raw`

DNSMOS SIG_raw

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `SIG_raw` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_bak_raw`

DNSMOS BAK_raw

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `BAK_raw` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos_ovrl_raw`

DNSMOS OVRL_raw

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `OVRL_raw` |
| Configuration | `source_file`, `primary_model`, `p808_model` |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `nisqa_mos`

NISQA Overall quality

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/gabrielmittag/NISQA) |
| Model family / head | `nisqa` / `mos` |
| Configuration | `source_dir`, `checkpoint` |

Requires the multidimensional nisqa.tar checkpoint. MOS, NOI, DIS, COL and LOUD are quality ratings; higher NOI means better noisiness quality, not greater noise energy. MOS-only/TTS checkpoints are not interchangeable five-head models.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `nisqa_noi`

NISQA Noisiness quality

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/gabrielmittag/NISQA) |
| Model family / head | `nisqa` / `noi` |
| Configuration | `source_dir`, `checkpoint` |

Requires the multidimensional nisqa.tar checkpoint. MOS, NOI, DIS, COL and LOUD are quality ratings; higher NOI means better noisiness quality, not greater noise energy. MOS-only/TTS checkpoints are not interchangeable five-head models.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `nisqa_dis`

NISQA Discontinuity quality

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/gabrielmittag/NISQA) |
| Model family / head | `nisqa` / `dis` |
| Configuration | `source_dir`, `checkpoint` |

Requires the multidimensional nisqa.tar checkpoint. MOS, NOI, DIS, COL and LOUD are quality ratings; higher NOI means better noisiness quality, not greater noise energy. MOS-only/TTS checkpoints are not interchangeable five-head models.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `nisqa_col`

NISQA Coloration quality

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/gabrielmittag/NISQA) |
| Model family / head | `nisqa` / `col` |
| Configuration | `source_dir`, `checkpoint` |

Requires the multidimensional nisqa.tar checkpoint. MOS, NOI, DIS, COL and LOUD are quality ratings; higher NOI means better noisiness quality, not greater noise energy. MOS-only/TTS checkpoints are not interchangeable five-head models.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `nisqa_loud`

NISQA Loudness quality

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/gabrielmittag/NISQA) |
| Model family / head | `nisqa` / `loud` |
| Configuration | `source_dir`, `checkpoint` |

Requires the multidimensional nisqa.tar checkpoint. MOS, NOI, DIS, COL and LOUD are quality ratings; higher NOI means better noisiness quality, not greater noise energy. MOS-only/TTS checkpoints are not interchangeable five-head models.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `utmos`

UTMOS22 strong

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/tarepan/SpeechMOS) |
| Model family / head | `utmos` / `mos` |
| Configuration | `source_dir`, `checkpoint` |

SpeechMOS conversion of UTMOS22 strong, not UTMOSv2. Keeps upstream time pooling and the 2*x+3 mapping. Source and weight fingerprints identify the model; native torchaudio resampling.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `sheet_ssqa`

SHEET SSL-MOS (model/config must be identified)

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/unilight/sheet) |
| Model family / head | `sheet_ssqa` / `mos` |
| Configuration | `source_dir`, `config_file`, `checkpoint`, `ssl_checkpoint` |

SHEET is a toolkit. The validated model is all7-sslmos-mdf-2337, checkpoint-86000steps, mean_net mode. Configuration, SSL backbone and scoring checkpoint jointly define its identity. Other SHEET models are not implied to be validated. Uses explicit soxr HQ to 16 kHz and original Predictor tensor input.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `speaker_similarity`

RawNet3 embedding cosine

| Property | Contract |
|---|---|
| Measurement | `speaker_identity` |
| Reference | `speaker_reference` |
| Output | `cosine`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://huggingface.co/espnet/voxcelebs12_rawnet3) |
| Model family / head | `speaker_similarity` / `cosine` |
| Configuration | `config_file`, `checkpoint` |

ESPnet voxcelebs12 RawNet3 embeddings at 16 kHz. Cosine has theoretical range [-1,1]; it is not clamped to [0,1]. It is not speaker-verification accuracy, EER or a calibrated probability.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `phoneme_similarity`

1 minus character edit rate of decoded IPA (not PER)

| Property | Contract |
|---|---|
| Measurement | `content_similarity` |
| Reference | `matching_waveform` |
| Output | `ratio`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft) |
| Model family / head | `phoneme_similarity` / `similarity` |
| Configuration | `model_dir` |

Preserves the legacy definition: predict IPA, remove spaces, then compute 1 minus Unicode-character edit distance divided by reference character count. This is not phone-token PER, can be negative, and is not clamped.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `visqol_speech`

ViSQOL speech 16 kHz

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `aligned_waveform` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/google/visqol) |
| Model family / head | `visqol_speech` / `mos` |
| Configuration | `binary`, `checkpoint` |

Speech: 16 kHz lattice TFLite. Audio: 48 kHz SVR. Explicit soxr HQ and PCM16; inputs must have equal original rate/length and amplitudes within [-1,1]. No hidden cropping or peak normalization.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `visqol_audio`

ViSQOL audio 48 kHz

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `aligned_waveform` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/google/visqol) |
| Model family / head | `visqol_audio` / `mos` |
| Configuration | `binary`, `checkpoint` |

Speech: 16 kHz lattice TFLite. Audio: 48 kHz SVR. Explicit soxr HQ and PCM16; inputs must have equal original rate/length and amplitudes within [-1,1]. No hidden cropping or peak normalization.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `speechbert_precision`

SpeechBERTScore precision; HuBERT layer 8 default

| Property | Contract |
|---|---|
| Measurement | `content_similarity` |
| Reference | `matching_waveform` |
| Output | `cosine`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Model family / head | `speechbert` / `precision` |
| Configuration | `source_dir`, `model_dir`, `layer` |

Original SpeechBERTScore feature matching; HuBERT base hidden layer 8 in the validated profile. Exposes precision, recall and harmonic F1 separately. Learned frame similarity is not a timestamp error.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `speechbert_recall`

SpeechBERTScore recall; HuBERT layer 8 default

| Property | Contract |
|---|---|
| Measurement | `content_similarity` |
| Reference | `matching_waveform` |
| Output | `cosine`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Model family / head | `speechbert` / `recall` |
| Configuration | `source_dir`, `model_dir`, `layer` |

Original SpeechBERTScore feature matching; HuBERT base hidden layer 8 in the validated profile. Exposes precision, recall and harmonic F1 separately. Learned frame similarity is not a timestamp error.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `speechbert_f1`

SpeechBERTScore f1; HuBERT layer 8 default

| Property | Contract |
|---|---|
| Measurement | `content_similarity` |
| Reference | `matching_waveform` |
| Output | `cosine`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Model family / head | `speechbert` / `f1` |
| Configuration | `source_dir`, `model_dir`, `layer` |

Original SpeechBERTScore feature matching; HuBERT base hidden layer 8 in the validated profile. Exposes precision, recall and harmonic F1 separately. Learned frame similarity is not a timestamp error.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `whisper_wer`

Whisper ASR WER against ground-truth text

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/huggingface/transformers) |
| Model family / head | `whisper_wer` / `wer` |
| Configuration | `model_dir`, `language`, `beam_size` |

Whisper large-v3, English, beam_size=5, deterministic generation, clips <=30 s. WER uses reference text; dWER uses clean-reference ASR text. EnglishTextNormalizer({}) precedes shared normalization/MeetEval. The runtime fixture does not establish ASR accuracy on a benchmark.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `whisper_dwer`

Whisper ASR WER against ASR transcript of clean reference; not ground-truth WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `matching_waveform` |
| Output | `percent`; `lower_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/huggingface/transformers) |
| Model family / head | `whisper_dwer` / `wer` |
| Configuration | `model_dir`, `language`, `beam_size` |

Whisper large-v3, English, beam_size=5, deterministic generation, clips <=30 s. WER uses reference text; dWER uses clean-reference ASR text. EnglishTextNormalizer({}) precedes shared normalization/MeetEval. The runtime fixture does not establish ASR accuracy on a benchmark.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `orcwer`

Optimal reference combination WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | multispeaker_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `tcorcwer`

Time-constrained ORC-WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | multispeaker_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `mimower`

Multi-input multi-output WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | multispeaker_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `tcmimower`

Time-constrained MIMO-WER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | multispeaker_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `greedy_dicpwer`

Greedy diarization-invariant cpWER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | multispeaker_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `greedy_ditcpwer`

Greedy diarization-invariant tcpWER

| Property | Contract |
|---|---|
| Measurement | `recognition` |
| Reference | `speaker_transcript` |
| Output | `percent`; `lower_is_better` |
| Task tags | multispeaker_asr |
| Source | [Upstream implementation](https://github.com/fgnt/meeteval) |

MeetEval 0.4.3 with the preserved nfkc-casefold-v1 profile. Report recording scope, token unit, speaker assignment and timing policy. TS-ASR scores a predetermined target. Time-constrained variants use explicit collars and pseudo-word timing. Greedy DI methods are identified as approximate algorithms.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `bss_sdr`

BSS signal-to-distortion ratio

| Property | Contract |
|---|---|
| Measurement | `signal_fidelity` |
| Reference | `aligned_multisource_waveform` |
| Output | `dB`; `higher_is_better` |
| Task tags | separation, tse |
| Source | [Upstream implementation](https://github.com/fakufaku/fast_bss_eval) |

fast-bss-eval upstream implementation. SI-SDR uses zero_mean=True; SI-SDRi subtracts the mixture baseline. BSS metrics use a complete [sources,samples] matrix, default filter_length=512, zero_mean=False and explicit permutation. Infinite/degenerate results are reported rather than clipped.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `bss_sir`

BSS signal-to-interference ratio

| Property | Contract |
|---|---|
| Measurement | `signal_fidelity` |
| Reference | `aligned_multisource_waveform` |
| Output | `dB`; `higher_is_better` |
| Task tags | separation, tse |
| Source | [Upstream implementation](https://github.com/fakufaku/fast_bss_eval) |

fast-bss-eval upstream implementation. SI-SDR uses zero_mean=True; SI-SDRi subtracts the mixture baseline. BSS metrics use a complete [sources,samples] matrix, default filter_length=512, zero_mean=False and explicit permutation. Infinite/degenerate results are reported rather than clipped.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `bss_sar`

BSS signal-to-artifacts ratio

| Property | Contract |
|---|---|
| Measurement | `signal_fidelity` |
| Reference | `aligned_multisource_waveform` |
| Output | `dB`; `higher_is_better` |
| Task tags | separation, tse |
| Source | [Upstream implementation](https://github.com/fakufaku/fast_bss_eval) |

fast-bss-eval upstream implementation. SI-SDR uses zero_mean=True; SI-SDRi subtracts the mixture baseline. BSS metrics use a complete [sources,samples] matrix, default filter_length=512, zero_mean=False and explicit permutation. Infinite/degenerate results are reported rather than clipped.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `plcc`

Pearson linear correlation

| Property | Contract |
|---|---|
| Measurement | `rating_agreement` |
| Reference | `paired_subjective_ratings` |
| Output | `correlation`; `higher_is_better` |
| Task tags | quality_prediction |
| Source | [Upstream implementation](https://docs.scipy.org/doc/scipy/reference/stats.html) |

SciPy on paired rating arrays. At least three finite pairs, neither constant. Pearson, Spearman and Kendall tau-b use no hidden nonlinear mapping. This is a dataset-level statistic, not an utterance score to average.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `srcc`

Spearman rank correlation

| Property | Contract |
|---|---|
| Measurement | `rating_agreement` |
| Reference | `paired_subjective_ratings` |
| Output | `correlation`; `higher_is_better` |
| Task tags | quality_prediction |
| Source | [Upstream implementation](https://docs.scipy.org/doc/scipy/reference/stats.html) |

SciPy on paired rating arrays. At least three finite pairs, neither constant. Pearson, Spearman and Kendall tau-b use no hidden nonlinear mapping. This is a dataset-level statistic, not an utterance score to average.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `ktau`

Kendall tau-b

| Property | Contract |
|---|---|
| Measurement | `rating_agreement` |
| Reference | `paired_subjective_ratings` |
| Output | `correlation`; `higher_is_better` |
| Task tags | quality_prediction |
| Source | [Upstream implementation](https://docs.scipy.org/doc/scipy/reference/stats.html) |

SciPy on paired rating arrays. At least three finite pairs, neither constant. Pearson, Spearman and Kendall tau-b use no hidden nonlinear mapping. This is a dataset-level statistic, not an utterance score to average.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `vad_error`

Speech-activity detection error rate

| Property | Contract |
|---|---|
| Measurement | `speech_activity` |
| Reference | `speaker_annotation` |
| Output | `percent`; `lower_is_better` |
| Task tags | vad, diarization |
| Source | [Upstream implementation](https://github.com/pyannote/pyannote-metrics) |

pyannote.metrics time-coverage components. Speaker identity is ignored. Specify UEM, collar and overlap behavior; accumulate time components for corpus scores.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `vad_precision`

Speech-activity detection precision

| Property | Contract |
|---|---|
| Measurement | `speech_activity` |
| Reference | `speaker_annotation` |
| Output | `percent`; `higher_is_better` |
| Task tags | vad, diarization |
| Source | [Upstream implementation](https://github.com/pyannote/pyannote-metrics) |

pyannote.metrics time-coverage components. Speaker identity is ignored. Specify UEM, collar and overlap behavior; accumulate time components for corpus scores.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `vad_recall`

Speech-activity detection recall

| Property | Contract |
|---|---|
| Measurement | `speech_activity` |
| Reference | `speaker_annotation` |
| Output | `percent`; `higher_is_better` |
| Task tags | vad, diarization |
| Source | [Upstream implementation](https://github.com/pyannote/pyannote-metrics) |

pyannote.metrics time-coverage components. Speaker identity is ignored. Specify UEM, collar and overlap behavior; accumulate time components for corpus scores.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `vad_accuracy`

Speech-activity detection accuracy

| Property | Contract |
|---|---|
| Measurement | `speech_activity` |
| Reference | `speaker_annotation` |
| Output | `percent`; `higher_is_better` |
| Task tags | vad, diarization |
| Source | [Upstream implementation](https://github.com/pyannote/pyannote-metrics) |

pyannote.metrics time-coverage components. Speaker identity is ignored. Specify UEM, collar and overlap behavior; accumulate time components for corpus scores.

**Evidence:** actual standard-library invocation with direct upstream comparison or an analytic fixture, plus the associated semantic tests.

## `scoreq`

Deprecated alias for scoreq_natural_ref; use explicit metric ID

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `nonmatching_waveform`, `matching_waveform` |
| Output | `embedding_distance`; `lower_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/alessandroragano/scoreq) |
| Model family / head | `scoreq_natural_ref` / `score` |
| Configuration | `checkpoint`, `reference_kind (REF only)` |
| Alias | Use `scoreq_natural_ref` in new experiments |

Choose natural/synthetic and nr/ref with the matching checkpoint. NR predicts MOS; REF is Euclidean embedding distance. Declare matching or nonmatching reference for natural REF; this synthetic REF profile requires nonmatching reference. Official preprocessing/predict uses an explicit local ONNX session.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `dnsmos`

Deprecated alias for dnsmos_ovrl; use explicit metric ID

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) |
| Model family / head | `dnsmos` / `OVRL` |
| Configuration | `source_file`, `primary_model`, `p808_model` |
| Alias | Use `dnsmos_ovrl` in new experiments |

Non-personalized profile. SIG/BAK/OVRL are calibrated outputs, with their three raw outputs also exposed; P808_MOS comes from a separate model. Explicit soxr HQ to 16 kHz, followed by official window/repetition/polynomial/averaging code.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `nisqa`

Deprecated alias for nisqa_mos; use explicit metric ID

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `none` |
| Output | `predicted_rating`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/gabrielmittag/NISQA) |
| Model family / head | `nisqa` / `mos` |
| Configuration | `source_dir`, `checkpoint` |
| Alias | Use `nisqa_mos` in new experiments |

Requires the multidimensional nisqa.tar checkpoint. MOS, NOI, DIS, COL and LOUD are quality ratings; higher NOI means better noisiness quality, not greater noise energy. MOS-only/TTS checkpoints are not interchangeable five-head models.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `speechbert_score`

Deprecated alias for speechbert_precision; use explicit metric ID

| Property | Contract |
|---|---|
| Measurement | `content_similarity` |
| Reference | `matching_waveform` |
| Output | `cosine`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Model family / head | `speechbert` / `precision` |
| Configuration | `source_dir`, `model_dir`, `layer` |
| Alias | Use `speechbert_precision` in new experiments |

Original SpeechBERTScore feature matching; HuBERT base hidden layer 8 in the validated profile. Exposes precision, recall and harmonic F1 separately. Learned frame similarity is not a timestamp error.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `visqol`

Deprecated alias for visqol_speech; use explicit metric ID

| Property | Contract |
|---|---|
| Measurement | `perceptual_quality` |
| Reference | `aligned_waveform` |
| Output | `predicted_mos`; `higher_is_better` |
| Task tags | enhancement, tse, separation, codec, tts, voice_conversion |
| Source | [Upstream implementation](https://github.com/google/visqol) |
| Model family / head | `visqol_speech` / `mos` |
| Configuration | `binary`, `checkpoint` |
| Alias | Use `visqol_speech` in new experiments |

Speech: 16 kHz lattice TFLite. Audio: 48 kHz SVR. Explicit soxr HQ and PCM16; inputs must have equal original rate/length and amplitudes within [-1,1]. No hidden cropping or peak normalization.

**Evidence:** real audio execution, declared outputs returned, and rejection of short/stereo/silent/missing-file inputs. Model-specific upstream parity and identity checks are recorded individually in the matrix.

## `speechbert_mhubert_precision`

SpeechBERTScore mHuBERT-147 layer 8 precision

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | cosine; higher_is_better |
| Implementation | DiscreteSpeechMetrics algorithm with utter-project/mHuBERT-147 |
| Source | [Upstream](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Required | reference and hypothesis audio paths; local mHuBERT-147 model_dir; official DiscreteSpeechMetrics source_dir; layer=8; mono; >=1 second |

Different encoder from HuBERT-base SBS; scores are not interchangeable. Full precision, recall and F1 retained.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `speechbert_mhubert_recall`

SpeechBERTScore mHuBERT-147 layer 8 recall

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | cosine; higher_is_better |
| Implementation | DiscreteSpeechMetrics algorithm with utter-project/mHuBERT-147 |
| Source | [Upstream](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Required | reference and hypothesis audio paths; local mHuBERT-147 model_dir; official DiscreteSpeechMetrics source_dir; layer=8; mono; >=1 second |

Different encoder from HuBERT-base SBS; scores are not interchangeable. Full precision, recall and F1 retained.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `speechbert_mhubert_f1`

SpeechBERTScore mHuBERT-147 layer 8 f1

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | cosine; higher_is_better |
| Implementation | DiscreteSpeechMetrics algorithm with utter-project/mHuBERT-147 |
| Source | [Upstream](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) |
| Required | reference and hypothesis audio paths; local mHuBERT-147 model_dir; official DiscreteSpeechMetrics source_dir; layer=8; mono; >=1 second |

Different encoder from HuBERT-base SBS; scores are not interchangeable. Full precision, recall and F1 retained.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `speaker_similarity_wavlm`

WavLM-base-plus-SV x-vector cosine

| Property | Contract |
|---|---|
| Measurement | speaker_identity |
| Reference | speaker_reference |
| Output | cosine; higher_is_better |
| Implementation | Transformers WavLMForXVector |
| Source | [Upstream](https://huggingface.co/microsoft/wavlm-base-plus-sv) |
| Required | reference speaker audio and hypothesis audio; local WavLM-base-plus-SV model_dir; mono; >=1 second |

Cosine is in [-1,1], not calibrated probability or EER. Not interchangeable with RawNet3 or WavLM-large ECAPA.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `lps_phone`

Levenshtein Phoneme Similarity (phone-token profile)

| Property | Contract |
|---|---|
| Measurement | content_similarity |
| Reference | matching_waveform |
| Output | ratio; higher_is_better |
| Implementation | wav2vec2-lv-60-espeak-cv-ft + phone-token Levenshtein |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2026_challenge_track1/blob/main/evaluation_metrics/calculate_phoneme_similarity.py) |
| Required | hypothesis audio file; explicit local deployment config; reference |

1 - edit_distance / reference phone count; may be negative. Different from legacy IPA Unicode-character phoneme_similarity. Empty reference recognition is a failure; model-derived phones are not manual labels.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `plcmos_v2`

PLCMOS v2 final model

| Property | Contract |
|---|---|
| Measurement | perceptual_quality |
| Reference | none |
| Output | predicted_mos; higher_is_better |
| Implementation | Microsoft SpeechMOS 0.0.1.1 PLCMOS.get_mos |
| Source | [Upstream](https://pypi.org/project/speechmos/0.0.1.1/) |
| Required | hypothesis audio path; official SpeechMOS plcmos.py source_file; matching local ONNX checkpoint; seed=0; embed_rounds=15; mono; >=1 second; CPU |

Packet-loss-concealment MOS predictor; not established for arbitrary distortions. Final and validation checkpoints have different training/holdout scope. Seeded finite-rater sampling; scores depend on seed and repetition count.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `plcmos_v2_val`

PLCMOS v2 validation model

| Property | Contract |
|---|---|
| Measurement | perceptual_quality |
| Reference | none |
| Output | predicted_mos; higher_is_better |
| Implementation | Microsoft SpeechMOS 0.0.1.1 PLCMOS.get_mos |
| Source | [Upstream](https://pypi.org/project/speechmos/0.0.1.1/) |
| Required | hypothesis audio path; official SpeechMOS plcmos.py source_file; matching local ONNX checkpoint; seed=0; embed_rounds=15; mono; >=1 second; CPU |

Packet-loss-concealment MOS predictor; not established for arbitrary distortions. Final and validation checkpoints have different training/holdout scope. Seeded finite-rater sampling; scores depend on seed and repetition count.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `lsd_urgent`

URGENT gain-fitted natural-log spectral distance

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | natural_log_power_ratio; lower_is_better |
| Implementation | librosa STFT |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `lsd_db`

Log-spectral distance in dB (no gain fit)

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | dB; lower_is_better |
| Implementation | librosa STFT |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `mcd_urgent`

URGENT MCD with gain fit and c0

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | dB; lower_is_better |
| Implementation | pysptk mcep + fastdtw |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `mcd_dtw_c1`

SPTK MCD with DTW on c1..order (no gain fit)

| Property | Contract |
|---|---|
| Measurement | signal_fidelity |
| Reference | aligned_waveform |
| Output | dB; lower_is_better |
| Implementation | pysptk mcep + fastdtw |
| Source | [Upstream](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics) |
| Required | reference; hypothesis; sample_rate; equal-length finite non-silent mono audio |

Frame, gain, log-base and coefficient conventions are part of the metric ID. MCD uses DTW; neither MCD nor magnitude LSD directly measures timing or phase fidelity.

Protocol details: [v0.4 profiles](EXPANSION_PROFILES.md). Evidence: [v0.4 validation](../validation/expansion-v0.4.json).

## `aecmos_16k_echo`

Microsoft aecmos_16k: echo_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_16k_deg`

Microsoft aecmos_16k: deg_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_16k_scenarioless_echo`

Microsoft aecmos_16k_scenarioless: echo_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_16k_scenarioless_deg`

Microsoft aecmos_16k_scenarioless: deg_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_48k_echo`

Microsoft aecmos_48k: echo_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `aecmos_48k_deg`

Microsoft aecmos_48k: deg_mos

- Dimension: `perceptual_quality`; reference: `aec_triplet`.
- Output: `predicted_MOS`, `higher_is_better`; scope: `recording`.
- Required: `farend`, `microphone`, `hypothesis`, `config`, `explicit talk_type except scenarioless`.
- [Upstream source](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Three synchronous native-rate mono files, equal lengths, 1–20 seconds; no hidden resampling, cropping or gain fit. st=far-end only, nst=near-end only, dt=double-talk; scenario averages must remain stratified. DEG measures other degradations. Do not average ECHO and DEG into a synthetic overall MOS. Requires exactly one onnxruntime==1.16.3 or onnxruntime-gpu==1.16.3 distribution.

## `erle`

Echo return loss enhancement over explicit far-end-only intervals

- Dimension: `echo_attenuation`; reference: `echo_or_farend_only_microphone`.
- Output: `dB`, `higher_is_better`; scope: `recording`.
- Required: `reference`, `hypothesis`, `sample_rate`, `farend_only_regions`, `signal_definition`.
- [Upstream source](https://www.microsoft.com/en-us/research/publication/aecmos-a-speech-quality-assessment-metric-for-echo-impairment/); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Not defined as an echo-only measure during double-talk. Microphone-based ERLE includes noise; label this signal definition explicitly. Batches pool energies, not per-recording dB. Zero residual returns infinite_result and null.

## `eer`

Tie-aware interpolated equal error rate

- Dimension: `speaker_identity`; reference: `trial_labels`.
- Output: `percent`, `lower_is_better`; scope: `dataset`.
- Required: `scores`, `labels`.
- [Upstream source](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Whole trial list, both classes required; never average per-utterance EER/minDCF. Labels 1=target and 0=nontarget. Score direction is explicit. Ties share one operating point. EER uses linear ROC interpolation, which can differ from closest empirical-point conventions.

## `min_dcf`

Minimum detection cost with explicit prior

- Dimension: `speaker_identity`; reference: `trial_labels`.
- Output: `normalized_cost_or_cost`, `lower_is_better`; scope: `dataset`.
- Required: `scores`, `labels`, `p_target`.
- [Upstream source](https://www.nist.gov/document/nistsre10evalplan-r6pdf); [exact profile and examples](AEC_VERIFICATION.md); [validation](../validation/aec-verification-v0.5.json).

Whole trial list, both classes required; never average per-utterance EER/minDCF. Labels 1=target and 0=nontarget. Score direction is explicit. Ties share one operating point. Default costs 1/1; normalized=True. p_target is mandatory; minDCF is an oracle sweep, not deployment-threshold actual DCF.
