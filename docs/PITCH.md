# Pitch and voiced/unvoiced evaluation

These metrics measure acoustic feature fidelity to a particular reference recording. They do not measure naturalness directly. A natural TTS rendition may have a different pitch contour or duration from the reference. Use them with perceptual quality, intelligibility and speaker-identity measures rather than treating a low pitch error as a complete quality assessment.

There is no single universal official V/UV or F0 evaluation protocol. The mathematical reductions are simple, but pitch extraction, time alignment, voicing decisions and aggregation determine the result. SpeechMetricHub therefore exposes a reconstruction profile and separately named upstream-compatible profiles. Results from different profiles are not interchangeable.

## Interfaces and provenance

| Metric ID | Profile | Reported value | Better |
|---|---|---|---|
| `vuv_f1` | SpeechMetricHub WORLD reconstruction profile | Voiced-positive F1, ratio [0, 1] | Higher |
| `f0_rmse` | Same reconstruction profile | RMSE on jointly voiced frames, Hz | Lower |
| `vuv_f1_amphion` | Amphion Parselmouth recipe | Voiced-positive F1, ratio [0, 1] | Higher |
| `f0_rmse_amphion` | Amphion Parselmouth recipe | RMSE on all aligned frames, Hz | Lower |
| `log_f0_rmse_espnet` | ESPnet WORLD / mel-cepstral DTW recipe | Natural-log F0 RMSE on jointly voiced frames, dimensionless | Lower |

The unqualified IDs are explicitly **SpeechMetricHub-defined protocols**, not claims of a universal standard. The named profiles follow these pinned public implementations:

- Amphion revision [`26f6883110181f1dbfe95c70a7c7dbaf4de5f42a`](https://github.com/open-mmlab/Amphion/tree/26f6883110181f1dbfe95c70a7c7dbaf4de5f42a): [V/UV counts](https://github.com/open-mmlab/Amphion/blob/26f6883110181f1dbfe95c70a7c7dbaf4de5f42a/evaluation/metrics/f0/v_uv_f1.py), [F0 RMSE](https://github.com/open-mmlab/Amphion/blob/26f6883110181f1dbfe95c70a7c7dbaf4de5f42a/evaluation/metrics/f0/f0_rmse.py), and [Parselmouth feature extraction](https://github.com/open-mmlab/Amphion/blob/26f6883110181f1dbfe95c70a7c7dbaf4de5f42a/utils/f0.py).
- ESPnet revision [`c573dfed21a3d64ce491a6f53748cc6b596097e5`](https://github.com/espnet/espnet/tree/c573dfed21a3d64ce491a6f53748cc6b596097e5): [`evaluate_f0.py`](https://github.com/espnet/espnet/blob/c573dfed21a3d64ce491a6f53748cc6b596097e5/egs2/TEMPLATE/asr1/pyscripts/utils/evaluate_f0.py).

The profiles reuse WORLD, Praat/Parselmouth, pysptk and the corresponding alignment libraries. Upstream source identities, dependency versions and direct execution evidence are recorded in [validation/pitch-v0.7.json](../validation/pitch-v0.7.json). See [THIRD_PARTY.md](../THIRD_PARTY.md) for attribution and separate dependency licenses.

## What the scores mean

Let the reference voicing flag be `v` and the hypothesis flag be `h`. Each is true where the extracted F0 is nonzero. Voiced is the positive class:

```text
TP = count(v and h)         FP = count(not v and h)
FN = count(v and not h)     TN = count(not v and not h)
F1 = 2 * TP / (2 * TP + FP + FN)
```

This is a **frame-level voiced-positive F1**, not macro-F1 over the two classes and not voice activity detection. Unvoiced speech such as /s/ is speech for VAD but unvoiced for this metric. Silence is also included in the unvoiced class under these profiles. An application needing a speech-only scoring region must define that region explicitly; the adapter does not automatically discard silence.

For `f0_rmse`, let `V` be the aligned frames where both F0 estimates are nonzero:

```text
F0 RMSE = sqrt(sum((hypothesis_F0[t] - reference_F0[t])**2 for t in V) / len(V))
```

`log_f0_rmse_espnet` substitutes `ln(F0)` for F0. Its output is not Hz, cents or semitones. `f0_rmse_amphion` uses all aligned frames, including zeros in unvoiced regions, so voicing disagreements also contribute to its RMSE.

A jointly voiced mask measures pitch accuracy where both systems have a pitch estimate. It can hide missing or spurious voicing: an output that retains only a few easy voiced frames may obtain a deceptively low RMSE. Always inspect F1 and the reported `reference_voiced_frames`, `hypothesis_voiced_frames`, `common_voiced_frames` and `common_voiced_fraction` alongside RMSE. A perfect F1 also does not imply accurate pitch: an octave error can preserve every voicing flag.

These are comparisons of **estimated** pitch and voicing. The extractor is not human ground truth, and errors can increase for noise, irregular phonation, very high/low pitch or multiple concurrent speakers. Use an isolated target stream rather than a multi-speaker mixture unless the experiment explicitly defines a monophonic interpretation.

## Exact preprocessing and alignment

### Synchronized reconstruction: `vuv_f1` and `f0_rmse`

- Inputs: mono files or finite normalized floating-point arrays. File sample rates must agree; arrays require `sample_rate`. Native rate must be at least 16 kHz. Inputs must have equal sample counts.
- WORLD Harvest runs on float64 waveforms. Defaults: `frame_period=5.0` milliseconds, `f0_min=50`, `f0_max=800` Hz.
- No implicit resampling, truncation, gain fitting, delay search or DTW. The model output must already share the reference time axis. If a codec has a known algorithmic delay, align it once using the declared system delay before evaluation and record that operation in the experiment.
- Voicing is `F0 != 0`. RMSE uses jointly voiced frames. This protocol measures temporal as well as pitch fidelity; it does not optimize a warp to make the output agree with the reference.

### Amphion compatibility: `vuv_f1_amphion` and `f0_rmse_amphion`

- The audio frontend follows librosa loading/resampling. `sample_rate=None` means the upstream librosa default of **22050 Hz**, not native-rate processing.
- Defaults: `hop_length=256` samples, `f0_min=50`, `f0_max=1100` Hz. Praat/Parselmouth uses autocorrelation pitch analysis with voicing threshold **0.6** and its native frame times; no additional frame padding is applied.
- `method="cut"` truncates the F0 sequences to their common length. It does not estimate or correct a delay. `method="dtw"` uses librosa DTW directly on F0, including unvoiced zeros.
- Only `need_mean=False` is supported in this profile. The optional upstream pitch-centering variant is not silently substituted under the same ID.
- RMSE includes all retained frames. The V/UV result exposes the same confusion counts as the upstream extraction function, with an explicit F1 reduction.

This is the **raw-Hz Amphion recipe with explicitly selected options**, not Amphion's command-line default. The pinned upstream launcher defaults to DTW and enabled pitch-centering. For the adapter's default profile, the matching upstream options are `--align_method cut --f0_subtract_mean False`, together with the same sample rate. To reproduce the adapter's `method="dtw"`, change upstream `--align_method` to `dtw` while keeping centering disabled. The upstream `need_mean` name is misleading: its enabled path applies a median-based pitch normalization, so it is excluded from this raw-Hz ID.

F0-based DTW can align away timing and voicing differences. Use it when reproducing that exact upstream recipe, not as the default assessment of a synchronized codec or vocoder. Cut alignment can omit a long unmatched tail; disclose the duration difference rather than interpreting the retained region as a full-duration score.

### ESPnet compatibility: `log_f0_rmse_espnet`

- Files only, with equal native sample rates; inputs are loaded as **int16**, matching the upstream script. There is no implicit cross-rate conversion.
- Defaults: `f0_min=40`, `f0_max=800` Hz, `n_fft=1024`, `n_shift=256` samples. WORLD Harvest's frame period is `1000 * n_shift / sample_rate` milliseconds.
- WORLD CheapTrick produces the spectral envelope; pysptk `sp2mc` produces mel-cepstra. With `mcep_dim=None` and `mcep_alpha=None`, the upstream sample-rate-specific values are used.
- FastDTW (radius 1, Euclidean distance over the mel-cepstral coefficients) supplies the alignment. This is a different alignment from Amphion's F0 DTW.
- Natural-log F0 RMSE is computed only where both aligned F0 values are nonzero. There is no StoneMask refinement or median-centering step in this profile.

The named compatibility contracts cover the supported input domain and options above. Invalid input, unsupported rates/options and undefined cases receive explicit statuses rather than copying upstream accidental exceptions, NaNs or short-input sentinel values.

## Undefined results and aggregation

Both-unvoiced signals have no positive examples and produce an undefined F1 (`status: "undefined_result"`, `value: null`), not a fabricated perfect score. If exactly one signal contains voiced frames, F1 is zero. No jointly voiced frames makes strict/log-F0 RMSE undefined; inspect coverage rather than replacing it with zero. The Amphion compatibility profile also returns an undefined result when both contours are entirely unvoiced. This is an explicit boundary-policy departure from upstream's numerical zero for all-zero contours, which would not establish speech quality.

Results retain confusion counts and squared-error sufficient statistics so aggregation can be audited. `evaluate_batch` pools TP/FP/FN for both F1 interfaces. For `f0_rmse`, it pools squared error and scored frames and then takes the square root. `f0_rmse_amphion` and `log_f0_rmse_espnet` instead use an utterance macro mean of the per-utterance RMSEs, preserving their upstream corpus convention. These are different statistics; do not average per-utterance F1 or substitute pooled RMSE for a named macro result. Undefined cases and input failures remain visible in the batch's coverage and completeness fields. Inspect `aggregation` and `counts` in the returned batch object.

## Usage

Install the optional CPU dependencies:

```bash
python -m pip install '.[pitch]'  # from a SpeechMetricHub repository checkout
```

No neural checkpoint or GPU is required. These calls use the public API; the existing `MetricHub.run()` and `MetricHub.evaluate()` methods accept the same metric IDs in a correctly refreshed deployment.

```python
from speechmetrichub import evaluate, run

# One extraction per input/profile is shared by the two outputs.
scores = evaluate(
    ["vuv_f1", "f0_rmse"],
    reference="reference.wav",
    hypothesis="reconstruction.wav",
)

# Reproduce an explicitly selected upstream recipe.
amphion = evaluate(
    ["vuv_f1_amphion", "f0_rmse_amphion"],
    reference="reference.wav",
    hypothesis="generated.wav",
    sample_rate=22050,
    method="cut",
)
espnet = run(
    "log_f0_rmse_espnet",
    reference="reference.wav",
    hypothesis="generated.wav",
)
```

Check `status` before reading `value`, retain `protocol`, `backend` and `details`, and do not mix scores with different extraction/alignment settings. The executable [example](../examples/pitch.py) prints the complete result objects. [The validation evidence](../validation/pitch-v0.7.json) distinguishes direct upstream numerical comparisons from synthetic semantic checks; it does not establish a universal correlation with human quality judgments.

## 中文使用说明

这五个接口属于“基频与清浊音特征保真度”。`vuv_f1` 和 `f0_rmse` 用于时间对应的重建音频，默认不裁剪、不找延迟、不做 DTW；它们是明确命名和记录的 SpeechMetricHub 协议。带 `_amphion` 或 `_espnet` 的接口用于复现对应上游口径，不能把数值与其他协议直接混合。

F1 越高越好；F0 RMSE 越低越好，但必须同时检查有效浊音帧覆盖率。`log_f0_rmse_espnet` 是自然对数域误差，单位不是 Hz。自由韵律 TTS 可以产生与参考不同但自然的语调，因此这组指标不能独立代表自然度。真实音频对照、上游一致性及边界条件的验证结果见上面的验证报告。
