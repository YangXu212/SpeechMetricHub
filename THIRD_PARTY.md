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
