# Documentation

SpeechMetricHub separates **what is measured** from **what reference is needed** and **which tasks might use it**. Read the relevant protocol guide before comparing numbers across papers or systems.

## Getting started

1. [Installation](INSTALLATION.md) — optional scorer groups and dependency pins.
2. [Python and CLI API](API.md) — `run`, `evaluate`, `evaluate_batch`, `compare_recognition`, and CLI usage.
3. [Metric catalog](METRICS.md) — every canonical variant, alias, unit, direction, and limitation.
4. [Evaluation protocols](PROTOCOLS.md) — normalization, alignment, timing collars, and corpus aggregation.
5. [Runnable examples](../examples/README.md) — ready-to-run JSON and CLI templates.

## Protocol guides

- [Whisper ASR profiles](WHISPER_ASR.md) — recommended OpenAI Whisper (`whisper_*_en_openai`), upgraded HF Whisper v3 (`whisper_*_hf_v3`), and legacy compatibility profiles.
- [Cohere Transcribe ASR](COHERE_ASR.md) and [Explicit Cohere profiles & corpus comparison](COHERE_PROFILES.md) — offline native Transformers 5.4 worker, Whisper/basic cleaners, truncation handling, and `compare_recognition`.
- [Pitch and voicing](PITCH.md) — V/UV F1 and F0 RMSE across WORLD, Amphion, and ESPnet recipes.
- [AEC and speaker verification](AEC_VERIFICATION.md) — AECMOS ECHO/DEG profiles, ERLE energy pooling, EER, and minDCF.
- [Spectral and expansion profiles](EXPANSION_PROFILES.md) — mHuBERT SpeechBERTScore, phone-token LPS, WavLM-base-plus-SV, PLCMOS, and LSD/MCD profiles.

## Deployment, validation and maintenance

- [Model setup and artifacts](MODELS.md) — all pretrained model families, required local files, and validation commands.
- [Shared cluster deployment](SHARED_DEPLOYMENT.md) — pinned full environment, `MetricHub`, and shared CLI entry points.
- [Deployment locks](DEPLOYMENT_LOCKS.md) — artifact/environment SHA-256 manifests and isolated worker locks.
- [Validation evidence](../validation/README.md) — versioned real-audio execution and upstream parity reports.
- [Architecture and extension guide](EXTENDING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Windows build notes](../WINDOWS_BUILD.md).
- [Changelog](../CHANGELOG.md) · [Roadmap](ROADMAP.md) · [Third-party attribution](../THIRD_PARTY.md) · [Security](../SECURITY.md).

## 中文资料

[中文简介](../README.zh-CN.md) · [中文指标卡](METRICS.zh-CN.md) · [部署说明](DEPLOYMENT.md) · [验证记录](../validation/README.zh-CN.md)
