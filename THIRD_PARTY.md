# Upstream implementations and artifacts

This library does not create a universal benchmark standard. It integrates existing implementations and records the exact local evaluation protocol. Dataset/challenge rules still determine normalization, scoring regions, reference quality and aggregation.

| Implementation | Role | Upstream |
|---|---|---|
| MeetEval | WER/CER, speaker-permutation and time-constrained/multistream errors | https://github.com/fgnt/meeteval |
| kaldialign | Alignment display and IPA character edit distance | https://github.com/csukuangfj/kaldialign |
| pyannote.metrics | Diarization and speech activity | https://github.com/pyannote/pyannote-metrics |
| fast-bss-eval | SI-SDR and BSS SDR/SIR/SAR | https://github.com/fakufaku/fast_bss_eval |
| PESQ, pystoi | Perceptual quality / intelligibility | https://github.com/ludlows/PESQ ; https://github.com/mpariente/pystoi |
| ViSQOL | Speech and general audio quality | https://github.com/google/visqol |
| Audiobox Aesthetics | CE, CU, PC, PQ | https://github.com/facebookresearch/audiobox-aesthetics |
| SCOREQ | Natural/synthetic, reference/no-reference | https://github.com/alessandroragano/scoreq |
| DNSMOS | SIG, BAK, OVRL, P808_MOS and raw heads | https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS |
| NISQA | Overall/noisiness/discontinuity/coloration/loudness | https://github.com/gabrielmittag/NISQA |
| SpeechMOS | UTMOS22 strong converted model | https://github.com/tarepan/SpeechMOS |
| SHEET | Configurable SSL-MOS inference | https://github.com/unilight/sheet |
| DiscreteSpeechMetrics | SpeechBERTScore precision/recall/F1 | https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics |
| ESPnet RawNet3 | Speaker embedding cosine | https://huggingface.co/espnet/voxcelebs12_rawnet3 |
| Transformers | Whisper and phoneme recognizer execution | https://github.com/huggingface/transformers |

Model weights, upstream source and executables are not redistributed in this wheel. Check their separate licenses before redistribution or commercial use. In particular, Audiobox code/weights and PESQ have their own conditions; this project's MIT license does not override them. Source revisions and artifact SHA-256 values used in validation are in the deployment manifest and detailed reports.

The compatibility loader for SHEET injects a local SSL checkpoint only; its network and forward computation are upstream. SCOREQ uses the official preprocessing/predict methods with an explicit ONNX session. SpeechBERTScore uses the official feature matching and pooling with a local HuBERT model. DNSMOS receives a 16 kHz float WAV so its historical librosa resampling API is not invoked. These initialization/I/O choices are included in result metadata.

## v0.4 sources

- Microsoft [SpeechMOS 0.0.1.1](https://pypi.org/project/speechmos/0.0.1.1/): PLCMOS preprocessing/inference, loaded from an explicitly supplied public source file. This is a different project from tarepan/SpeechMOS (UTMOS).
- [URGENT 2025](https://github.com/urgent-challenge/urgent2025_challenge/tree/main/evaluation_metrics): mathematical LSD and MCD conventions; upstream functions are independently invoked in validation.
- [URGENT 2026](https://github.com/urgent-challenge/urgent2026_challenge_track1/blob/main/evaluation_metrics/calculate_phoneme_similarity.py) and the [LPS authors](https://git.rz.tu-bs.de/ifn-public/LPS): phone-token LPS definition.
- [pysptk](https://github.com/r9y9/pysptk) and [fastdtw](https://github.com/slaypni/fastdtw): mel-cepstral analysis and alignment. The public SPTK/ESPnet-derived reference script credits Wen-Chin Huang and Tomoki Hayashi under Apache-2.0; it is used as an external validation reference, not vendored here.
- [mHuBERT-147](https://huggingface.co/utter-project/mHuBERT-147) and [WavLM-base-plus-SV](https://huggingface.co/microsoft/wavlm-base-plus-sv): independently provisioned pretrained encoders, each with its own model-card terms.

No internal lab code tree or model weights are included in this repository. Public source hashes and artifact fingerprints accompany the validation report. New adapters do not grant redistribution rights to upstream materials.

## v0.5 AEC and verification

- [Microsoft speechmos / AECMOS](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local): upstream three-signal frontend and three checkpoints, ECHO/DEG outputs; public package 0.0.1.1. Source and weights are provisioned separately, not redistributed here.
- [scikit-learn ROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html): complete tie-aware operating points, version 1.5.2. EER interpolation and NIST-style minDCF reductions are explicitly defined in our profile.
- [NIST SRE detection-cost construction](https://www.nist.gov/document/nistsre10evalplan-r6pdf): costs and prior must be reported; no claim of one universal NIST trial protocol.
- [ONNX Runtime CUDA](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html): isolated execution and provider profiling. AECMOS pins 1.16.3 for original-checkpoint compatibility.
