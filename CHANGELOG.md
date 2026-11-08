# Changelog

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
