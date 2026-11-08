# Evaluation expansion: research and integration plan

Planned on 2026-11-07, before implementation. This survey compared evaluation entry points used by two laboratory researchers, the shared evaluation toolkit, and the public upstream projects. Private scripts, machine paths, checkpoints and recordings are not redistributed.

## Decisions

| Candidate | Finding and integration decision | Measurement category |
|---|---|---|
| SBS / SpeechBERTScore | Existing HuBERT-base layer 8 P/R/F1 is retained. Add mHuBERT-147 layer 8 P/R/F1 as separate IDs; never substitute a model under an existing ID. | content_similarity |
| LPS | Existing `phoneme_similarity` removes spaces and counts IPA Unicode characters. Current URGENT uses space-delimited phone tokens. Add an explicit phone-token LPS and document the old character profile. | content_similarity |
| PLCMOS | Add explicit release/validation model profiles using the official SpeechMOS implementation and local ONNX artifacts. Inspect legacy intrusive/nonintrusive variants before deciding their supported scope. Seed and embedding repetitions must be reported. | perceptual_quality |
| WavLM SpkSim | Add WavLM-base-plus-SV x-vector cosine separately from RawNet3. Investigate WavLM-large/ECAPA fine-tuned and frozen variants; checkpoint architecture and preprocessing must be reproducible. | speaker_identity |
| LSD | The surveyed score uses least-squares gain fitting and natural-log power ratios, not dB. Keep that named profile separate from a fixed dB spectral-distance profile. | signal_fidelity |
| MCD | Use public ESPnet/SPTK conventions, with explicit frame parameters, sample-rate-dependent warp, DTW and inclusion/exclusion of coefficient 0. The surveyed profile includes coefficient 0. | signal_fidelity |
| SI-SNR / SDR | Audit mean removal, projection, filter length and clamping before reuse. Names alone do not establish equivalence to existing SI-SDR/BSS-SDR. | signal_fidelity |
| EmoSim | Emotion2vec cosine measures paralinguistic preservation. Requires a new `paralinguistic_similarity` category, nonmatching controls and scrutiny of score saturation; do not present as general quality. | proposed: paralinguistic_similarity |
| LID / LAcc | Requires ground-truth language IDs, a pinned classifier and explicit label mapping. An ASR model's inferred label is not ground truth. | proposed: language_identification |
| OWSM / Cohere / Whisper CER | Backend-specific recognition profiles need decoding, language and normalization definitions and appropriate model execution tests; they are not interchangeable WER algorithms. | recognition |
| SpeechBLEU / SpeechTokenDistance | Public sibling methods of SBS; quantizer/codebook identity and token preprocessing are required before admission. | content_similarity |
| 2f-model | A function name in a toolkit is insufficient: the inspected public function raises `NotImplementedError`. Do not register an unavailable metric. | perceptual_quality |

## Implementation rules

1. Preserve every released ID and default. Register different semantics as different IDs.
2. Classify by measurement construct; use task tags, reference conditions and model profiles as separate fields.
3. Reuse public upstream algorithms where practical; record sources and artifact identities. No copying private project trees into the public repository.
4. Missing artifacts/dependencies and invalid inputs must return a visible failure. Never turn failed inference into zero or silently omit a sample from a complete-set score.
5. Keep model execution offline and isolated. Validation uses the maintainer's own environment, CPU and bounded threads; shared source/model directories remain read-only.

## Admission and publication gates

- Execute every new callable interface on real speech, with identical and nonmatching/degraded controls where meaningful.
- Compare to an independent upstream call or a separately specified analytic reference; record tolerances and observed differences.
- Check wrong reference type, mismatched rates/lengths where relevant, stereo, silence, too-short and missing inputs.
- Re-run existing semantic/API tests and model regression checks for changed shared execution paths.
- Update metric cards, deployment templates, dependency extras, validation evidence and changelog together.
- Build/install the wheel, run GitHub CI, then publish a versioned release. Only passed interfaces count as supported; investigated candidates remain visibly separate.

## Public sources

- [URGENT 2026 evaluation scripts](https://github.com/urgent-challenge/urgent2026_challenge_track1/tree/main/evaluation_metrics)
- [LPS authors' implementation](https://git.rz.tu-bs.de/ifn-public/LPS)
- [DiscreteSpeechMetrics](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics)
- [SpeechMOS / PLCMOS](https://pypi.org/project/speechmos/)
- [WavLM-base-plus-SV model card](https://huggingface.co/microsoft/wavlm-base-plus-sv)
- [UniSpeech speaker verification](https://github.com/microsoft/UniSpeech/tree/main/downstreams/speaker_verification)
- [ESPnet MCD evaluation](https://github.com/espnet/espnet/blob/master/utils/mcd_calculate.py)

The final admitted scope and measured outcomes are recorded in the release validation report, rather than inferred from this plan.
