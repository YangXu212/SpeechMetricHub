# Roadmap

These are candidates, not currently advertised callable interfaces. A new integration needs complete output coverage, a defined protocol, artifact identity and real execution evidence.

| Measurement area | Candidates | Protocol work required |
|---|---|---|
| Perceptual quality | POLQA/P.863, UTMOSv2, additional SHEET models, NISQA MOS-only/TTS, personalized DNSMOS | Licensed implementations, checkpoint identity, complete output variants |
| Intelligibility | HASPI/HASQI, SIIB | Hearing model parameters, alignment and implementation version |
| Acoustic fidelity | MCD, log-F0 RMSE, voiced/unvoiced error, LSD, FAD | Feature extraction, DTW, population statistics and aggregation |
| Content | SpeechBLEU, SpeechTokenDistance, phone-token PER | Unit model, codebook, tokenization and distance definitions |
| Echo/noise | ERLE, AECMOS, SRMR | Near/far-end and double-talk regions, signal definitions and model artifacts |
| Recognition/speakers | Official corpus profiles, word alignment, EER/minDCF | Official normalization, annotation validity, trial lists, priors and thresholds |
| Subjective evaluation | MUSHRA/ABX/MOS, confidence intervals and significance | Listener protocol, randomization, pairing and dependence assumptions |
| Execution | Persistent model workers, larger batch scheduling, additional platform/device validation | Resource isolation, deterministic behavior and measured throughput |

Improved model serving should not silently change the established evaluation profile. A registry placeholder is not a completed metric integration.
