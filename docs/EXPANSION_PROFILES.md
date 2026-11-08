# v0.4 profiles: names are part of the protocol

This release adds 11 canonical interfaces: 75 canonical variants and 5 compatibility aliases, organized under the existing 10 measurement dimensions. The [research plan](EXPANSION_PLAN.md) records the candidate survey; the [validation report](../validation/expansion-v0.4.json) records actual execution, not just registry coverage.

## SBS and LPS: content similarity

| IDs | Definition | Reference |
|---|---|---|
| `speechbert_precision`, `speechbert_recall`, `speechbert_f1` | Existing HuBERT-base layer 8; official DiscreteSpeechMetrics matching | Matching spoken content; no samplewise alignment needed |
| `speechbert_mhubert_precision`, `speechbert_mhubert_recall`, `speechbert_mhubert_f1` | Same matching algorithm, mHuBERT-147 layer 8 | Matching spoken content, multilingual encoder |
| `phoneme_similarity` | Existing `1 - character edit distance / reference IPA character count`, after deleting spaces | Reference audio decoded by the same phoneme recognizer |
| `lps_phone` | `1 - phone-token edit distance / reference phone count`, splitting the decoded phone sequence on whitespace | Same recognizer, distinct edit units |

`speechbert_score` remains the legacy alias of HuBERT precision. There is no ambiguous `sbs` or `lps` alias that might silently switch model or units. The phone-token profile follows the current [URGENT 2026 implementation](https://github.com/urgent-challenge/urgent2026_challenge_track1/blob/main/evaluation_metrics/calculate_phoneme_similarity.py); the surveyed older scripts use character distance. LPS can be negative, and an empty recognized reference is an error. An affricate or multi-character phoneme counts as one phone in the new profile.

All SBS heads in one `evaluate` call share the same inference. Precision takes the best reference-frame match for each hypothesis frame; recall reverses the reduction; F1 is their harmonic mean. Scores depend on encoder and layer. Multilingual pretraining does not establish equal validity across languages. Resampling is explicit soxr HQ to 16 kHz, with no gain normalization. Audio must be mono and at least one second; matching utterances can have different durations.

```python
from speechmetrichub import evaluate

results = evaluate(
    ["speechbert_mhubert_precision", "speechbert_mhubert_recall", "speechbert_mhubert_f1"],
    reference="reference.wav", hypothesis="generated.wav",
    configs={"speechbert_mhubert": {
        "source_dir": "/opt/upstream/DiscreteSpeechMetrics",
        "model_dir": "/models/mHuBERT-147", "layer": 8,
        "trusted_checkpoint": True, "device": "cpu", "threads": 2,
    }},
)
```

Use the public DiscreteSpeechMetrics implementation with the supplied local mHuBERT model; no private fork is required. Initialization is adapted to use local artifacts; scoring remains upstream.

## WavLM SpkSim: speaker identity

`speaker_similarity_wavlm` uses the official [microsoft/wavlm-base-plus-sv](https://huggingface.co/microsoft/wavlm-base-plus-sv) feature extractor and `WavLMForXVector` embeddings, then cosine similarity. Each waveform is independently resampled to 16 kHz. The feature extractor's normalization is preserved and its configuration is hashed.

Cosine is bounded by [-1,1], not a speaker-match probability. RawNet3 (`speaker_similarity`) and WavLM scores must not share a threshold. Reference selection must be fixed in advance; report whether it is enrollment audio or same-utterance clean speech. EER/minDCF require a genuine target/impostor trial set and are not inferred from a single cosine score.

WavLM-large + ECAPA fine-tuned/frozen checkpoints are distinct models. They remain candidates: the surveyed loader uses permissive state loading and implicit backbone provisioning; this release does not disguise them as the validated base-plus-SV interface.

## PLCMOS: perceptual quality

`plcmos_v2` and `plcmos_v2_val` expose separate local ONNX checkpoints using the public **Microsoft SpeechMOS 0.0.1.1** `PLCMOS.get_mos` implementation. This Microsoft package is distinct from tarepan's SpeechMOS used by UTMOS.

- The v2 final model is trained without the paper's holdout; the validation checkpoint has a different training split. They are not interchangeable.
- Default protocol: 16 kHz, ONNX CPU provider, 15 sampled rater embeddings, NumPy RandomState seed 0 in an isolated process. The seed and repetitions are part of the result.
- The scorer retains upstream STFT/features and averaging. No gain normalization or clamping is applied; samples outside [-1,1] are rejected.
- These are packet-loss-concealment quality predictors, not universal subjective MOS measurements.
- The public package contains the final checkpoint. A matching validation checkpoint must be separately provisioned; compare its SHA-256 with the evidence report. It is not redistributed here.

Install `.[models,plcmos]`. Obtain the public SpeechMOS wheel from its [versioned package page](https://pypi.org/project/speechmos/0.0.1.1/) and unpack it into a trusted source directory. Point `source_file` at `speechmos/plcmos.py` and `checkpoint` at the chosen ONNX file. The adapter uses an explicit session so the package's default path does not override the configured artifact.

Legacy PLCMOS v0/v0alpha intrusive/combined modes are not implemented by that public package's v2 class and are not advertised here. Adding them requires their original public implementation, mode-specific references and separate tests.

## LSD and MCD: signal fidelity

All four interfaces take `reference`, `hypothesis`, `sample_rate`. Inputs may be arrays or files. Files must match the declared rate. This release requires non-silent, finite, mono, equal-length inputs; it does not crop or search a delay. MCD subsequently uses DTW internally. Corpus aggregation is an utterance macro mean, not a pooled-frame mean.

| ID | Gain / feature convention | Unit |
|---|---|---|
| `lsd_urgent` | Least-squares fit of hypothesis to reference; natural-log power ratio using URGENT epsilon placements | Natural-log ratio, **not dB** |
| `lsd_db` | No gain fitting; difference of `10 log10(max(power, 1e-12))` | dB |
| `mcd_urgent` | Gain fitting; SPTK cepstrum; includes c0; FastDTW on all coefficients | dB |
| `mcd_dtw_c1` | No gain fitting; excludes c0; FastDTW on c1 through order | dB |

LSD uses a 32 ms periodic Hann window/FFT, 16 ms hop, centered zero padding, all one-sided frequency bins, RMS across frequency followed by mean across time. The URGENT profile fits gain with `dot(ref,hyp)/(dot(hyp,hyp)+1e-8)` and computes `ln(A²/(B+1e-8)²+1e-8)`. Its epsilon means identical inputs need not yield exactly zero. `lsd_db` is an explicitly defined engineering profile, not a claim of one universal LSD standard.

MCD uses 1024-sample SPTK Hamming windows, 256-sample hop, no padding or silence removal, float64 original-amplitude waveforms, `pysptk.mcep(etype=1, eps=1e-6)`, and FastDTW radius 1 with Euclidean local costs. The final distance is the path mean of `(10/ln(10))*sqrt(2*sum(delta_cepstrum²))`. Coefficients used for DTW and distance are identical. This is the [URGENT/SPTK profile](https://github.com/urgent-challenge/urgent2025_challenge/blob/main/evaluation_metrics/mcd_utils.py), not WORLD MCD or the older ESPnet int16/silence-filtered CLI profile.

| Rate (Hz) | Order | Warp alpha |
|---:|---:|---:|
| 8000 | 13 | 0.31 |
| 16000 | 23 | 0.42 |
| 22050 | 34 | 0.45 |
| 24000 | 34 | 0.46 |
| 32000 | 36 | 0.50 |
| 44100 | 39 | 0.53 |
| 48000 | 39 | 0.55 |

Install `.[spectral]`. A C/C++ compiler may be needed for pysptk and fastdtw. Magnitude LSD is insensitive to phase inversion; DTW MCD can hide timing errors. Use timing/recognition metrics alongside these scores when those errors matter.

## Other surveyed candidates

EmoSim, LAcc, OWSM/Cohere recognition, WavLM-large ECAPA, SpeechBLEU/TokenDistance and legacy PLCMOS modes are recorded in the [plan](EXPANSION_PLAN.md), not added as untested placeholders. EmoSim needs positive/negative controls before interpreting highly saturated cosines. LAcc needs an explicit language-label mapping and a pinned classifier. The 2f-model function found in the official script is unimplemented. SI-SNR naming is handled by documenting the mean-removal/projection convention of existing SI-SDR, not duplicating a name without a separate scoring definition.
