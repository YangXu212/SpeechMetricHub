# Roadmap

These are candidates, not currently advertised callable interfaces. A new integration needs complete output coverage, a defined protocol, artifact identity and real execution evidence.

| Measurement area | Candidates | Protocol work required |
|---|---|---|
| Perceptual quality | POLQA/P.863, UTMOSv2, additional SHEET models, NISQA MOS-only/TTS, personalized DNSMOS | Licensed implementations, checkpoint identity, complete output variants |
| Intelligibility | HASPI/HASQI, SIIB | Hearing model parameters, alignment and implementation version |
| Acoustic fidelity | Additional MCD/pitch extraction profiles, FAD | Feature extraction, alignment, population statistics and aggregation; [pitch/voicing profiles](PITCH.md) shipped in v0.7 |
| Content | SpeechBLEU, SpeechTokenDistance, phone-token PER | Unit model, codebook, tokenization and distance definitions |
| Echo/noise | SRMR and additional echo diagnostics | Signal definitions, room conditions and validity |
| Recognition/speakers | Official corpus profiles, word alignment, actual DCF and calibration | Official normalization, annotation validity, trial lists, priors and thresholds |
| Subjective evaluation | MUSHRA/ABX/MOS, confidence intervals and significance | Listener protocol, randomization, pairing and dependence assumptions |
| Execution | Persistent model workers, larger batch scheduling, additional platform/device validation | Resource isolation, deterministic behavior and measured throughput |

Improved model serving should not silently change the established evaluation profile. A registry placeholder is not a completed metric integration.

AECMOS, ERLE, EER and minDCF are implemented in v0.5; see [their exact profiles](AEC_VERIFICATION.md).

## Surveyed after v0.3

The [v0.4 integration plan](EXPANSION_PLAN.md) and [admitted profiles](EXPANSION_PROFILES.md) distinguish shipped interfaces from pending research. Remaining candidates include WavLM-large ECAPA (frozen/fine-tuned), emotion2vec cosine, language identification accuracy, OWSM/Cohere decoding profiles, and legacy PLCMOS intrusive modes. Emotion and language metrics would receive their own measurement dimensions when admitted; they are not relabeled as signal quality.
