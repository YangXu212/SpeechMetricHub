# Changelog

## 0.7.0 — 2026-11-10

- Add V/UV F1 and F0 RMSE with explicit WORLD reconstruction profiles, Amphion raw-Hz/voicing profiles and ESPnet log-F0 RMSE (five IDs).
- Share pitch extraction within multi-metric calls; pool confusion counts and squared errors for the reconstruction profiles. Keep upstream RMSE utterance aggregation explicit.
- Record effective parameters, versions, input hashes, voicing counts and scored-frame coverage. Undefined voicing support returns null rather than a fabricated perfect score.
- Pin source revisions and attribute adapted MIT/Apache recipes. Add Praat/Parselmouth 0.4.7 as a CPU dependency; no model download is needed.
- Add direct upstream parity checks on real audio, controlled pitch/voicing tests, and detailed [scientific protocol documentation](docs/PITCH.md).
- Preserve existing metric definitions. The registry now has 94 IDs / 89 canonical variants; prior 89-interface runtime evidence remains separately versioned.

## 0.6.0 — 2026-11-08

- Add a pinned Linux/Python 3.10 full environment derived from an independent Torch 2.8 clone, with all 89 registry IDs exercised in one interpreter.
- Reconcile ESPnet's NumPy/setuptools requirements with the original AECMOS/SCOREQ ONNX Runtime 1.16.3 profile. Keep one CPU ONNX distribution and retain Torch CUDA 12.8.
- Add `MetricHub`, a shared deployment entry-point generator, and the `SPEECHMETRICHUB_DEPLOYMENT` CLI default.
- Verify only requested model artifacts during scoring, retaining full environment checks and a separate full-deployment verification command.
- Stabilize dependency snapshots against optional imports that expose vendored distribution metadata.
- Add reproducible deployment instructions, per-interface runtime evidence and compatibility checks without changing metric definitions or counts.

## 0.5.0 — 2026-11-08

- Add AECMOS ECHO/DEG across 16k scenario, 16k scenarioless and 48k scenario profiles; exact upstream artifacts and compatible ONNX Runtime pin.
- Add explicit-region ERLE with energy pooling and visible undefined/infinite outcomes.
- Add dataset-level EER and minDCF with tie-aware ROC, score direction, explicit prior/costs and rejection of per-recording averaging.
- Add deployment lock/create/verify/load APIs and CLI; verify source, artifacts, Python and distribution versions before scoring.
- Add isolated Linux GPU library provisioning, requested-provider checks, real upstream CPU/GPU comparisons and CUDA-kernel profiling.
- Preserve all older metric IDs and protocols. The registry now contains 89 IDs, 84 canonical variants, 11 dimensions and 23 model families.


## 0.4.0 — 2026-11-07

- Add 11 validated metric interfaces: mHuBERT-147 SpeechBERTScore precision/recall/F1, phone-token LPS, WavLM-base-plus-SV cosine, PLCMOS v2 final/validation, URGENT natural-log LSD, dB LSD, URGENT MCD and c1-only DTW MCD.
- Preserve all prior IDs and scoring defaults. Distinguish phone-token LPS from legacy IPA-character similarity and model-specific SBS from a generic name.
- Add spectral/PLCMOS dependency extras, local-artifact deployment templates, the research/admission plan, exact profile definitions and repeatable real-model/parity/control harnesses.
- Expand semantic/API tests from 33 to 39; add real-speech, upstream/analytic parity, boundary, speaker positive/negative, RNG repeatability and artifact-mismatch evidence. Public CI includes the new spectral dependency stack; heavy model execution remains separately documented.
- No private lab code, audio or model weights are redistributed.

## 0.3.0 — First public SpeechMetricHub release

- Name and package the project as SpeechMetricHub, with a public `speechmetrichub` namespace and CLI.
- Keep the existing `speech_eval` API and `speech-eval` command for compatibility; preserve scoring algorithms and the v1 transcription profile.
- Add English/Chinese onboarding, a complete metric catalog, model configuration templates, protocol/API guides and a project banner.
- Add package-install smoke checks, documentation integrity checks, public API compatibility tests and repository contribution templates.
- Publish the existing v0.2 real-model evidence with its original scope, separately from public-release CI.

## 0.2.0

- Replace task-based primary grouping with measurement categories, independent reference requirements and task tags.
- Integrate native model interfaces; expose all four AE axes, all four SCOREQ domain/mode combinations, five NISQA dimensions, calibrated/raw DNSMOS outputs and all SpeechBERTScore outputs.
- Add ORC/tcORC, MIMO/tcMIMO, explicitly greedy DI metrics, VAD components, BSS SDR/SIR/SAR and rating correlations.
- Add isolated CPU-default model workers, offline artifacts, timeouts, model/source hashes, complete results and grouped multi-head inference.
- Correct DER/JER/VAD corpus aggregation and retain Whisper counts for micro WER.
- Add real per-interface runtime evidence, independent upstream parity, invalid-input and identity tests, clean environment installation, metric cards, doctor CLI and packaging/CI scaffolding.
- Keep five explicit migration aliases; workbench normalization and cached ASR scores retain the v1 protocol.

## 0.1.0

Initial MeetEval integration and optional scorer registry. External model bridge templates were not model runtime validation.
