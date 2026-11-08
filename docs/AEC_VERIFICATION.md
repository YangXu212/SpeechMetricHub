# AEC and speaker verification profiles

v0.5 adds nine explicit interfaces. Measurement dimensions remain separate from task tags:

| Dimension | IDs | Evaluation unit |
|---|---|---|
| `perceptual_quality` | `aecmos_16k_echo`, `aecmos_16k_deg`, `aecmos_16k_scenarioless_echo`, `aecmos_16k_scenarioless_deg`, `aecmos_48k_echo`, `aecmos_48k_deg` | Aligned audio triplet, fixed scenario/model |
| `echo_attenuation` | `erle` | Explicit far-end-only intervals; pooled energies across recordings |
| `speaker_identity` | `eer`, `min_dcf` | Complete labeled verification trial list |

## AECMOS

This adapter calls Microsoft's unmodified `speechmos==0.0.1.1` AECMOS frontend and original ONNX weights. ECHO estimates echo impairment; DEG estimates other degradations. Both are higher-is-better predicted MOS outputs. They are separate outputs, not components to average into an invented overall MOS. Read the [original paper](https://www.microsoft.com/en-us/research/publication/aecmos-a-speech-quality-assessment-metric-for-echo-impairment/) and [official local scorer](https://github.com/microsoft/AEC-Challenge/tree/main/AECMOS/AECMOS_local).

The files `farend`, `microphone`, and `hypothesis` mean playback/loopback, microphone before cancellation, and enhanced output. Supply finite, mono, equal-length audio at the named native sample rate, between **1 and 20 seconds**, with amplitudes in [-1,1]. The one-second minimum is this library's supported integration boundary, not a claim about perceptual validity for all short utterances. No hidden resampling, channel averaging, gain normalization, delay search, padding or truncation occurs. Segment longer recordings explicitly with the same boundaries for all signals. File length equality does not prove physical synchronization; callers remain responsible for capture alignment.

Scenario models require `talk_type="st"` (far-end single-talk), `"nst"` (near-end single-talk), or `"dt"` (double-talk). These exact tokens follow Microsoft's code. The scenarioless model requires `None`; it is a different checkpoint, not a missing-marker shortcut. Keep scenario/model/rate strata separate when reporting means. A silent enhanced output is scoreable; a silent microphone is rejected. A silent farend is allowed for near-end-only/scenarioless input, but contradicts a declared far-end-active scenario.

```python
from speechmetrichub import evaluate, load_deployment

scores = evaluate(
    ["aecmos_16k_echo", "aecmos_16k_deg"],
    farend="playback.wav", microphone="microphone.wav", hypothesis="enhanced.wav",
    talk_type="dt", configs=load_deployment("deployment.locked.json"),
)
```

One call shares the forward pass between the two heads. Checkpoint and source hashes are fixed to the published artifacts for each ID. Different weights require a new profile; a renamed file does not establish model identity. Inference stays offline. See [deployment locks](DEPLOYMENT_LOCKS.md) for provisioning and runtime checks.

## ERLE

ERLE = `10 * log10(sum(before²) / sum(after²))` over the explicitly supplied far-end-only sample intervals. Positive means lower residual energy. Preserve amplitude and alignment.

```python
from speechmetrichub import run

result = run(
    "erle", reference="mic.wav", hypothesis="enhanced.wav", sample_rate=16000,
    farend_only_regions=[[1.0, 4.0], [6.0, 8.0]],
    signal_definition="microphone_farend_only",
)
```

`signal_definition="isolated_echo"` means the reference and hypothesis contain the isolated echo and its residual. `"microphone_farend_only"` means the signals can include background noise: this is a microphone-based operational ratio, not pure echo attenuation. Regions are caller-supplied annotations; the scorer does not infer whether they are truly far-end single-talk. It is invalid to interpret microphone/output energy reduction during double-talk as ERLE, because near-end speech suppression can inflate it.

Intervals use seconds, converted with Python `round(seconds * sample_rate)` to half-open sample ranges. Empty, out-of-range, nonfinite and overlapping intervals are rejected. Gain >1 yields negative ERLE; values are never clipped. Zero reference energy returns `undefined_reference`; zero residual with positive reference returns `infinite_result` and JSON `null`, not an arbitrary epsilon or 100 dB.

`evaluate_batch("erle", records, ...)` pools numerator and denominator energies before taking the logarithm. It includes valid zero-residual recordings in this energy sum. It never averages utterance dB. Undefined-reference or invalid recordings make coverage incomplete and the overall value null. If all scored residuals are zero, coverage can be complete while the value remains null; the CLI returns nonzero. Report the coverage, signal definition and scored intervals with the result.

## EER and minDCF

Supply the **entire trial list**, numeric `labels` (1=target/same speaker, 0=nontarget/different speaker), and finite scalar scores. Both classes must occur. Optional `trial_ids` must be unique, nonempty strings. The adapter does not create enrollments, choose negatives, normalize speaker scores or infer labels from filenames.

```python
trials = dict(scores=[0.91, 0.82, 0.33, 0.74], labels=[1, 1, 0, 0],
              trial_ids=["e1-t1", "e2-t2", "e1-t3", "e2-t4"])
eer = run("eer", **trials)
dcf = run("min_dcf", **trials, p_target=0.01, c_miss=1.0, c_fa=1.0,
          normalized=True)
```

Default `score_direction="higher_is_target"` accepts scores `>= threshold`. Distance-like scores require `"lower_is_target"`, accepting `<= threshold`. Identical scores form one decision group. Rates come from `scikit-learn==1.5.2` `roc_curve(drop_intermediate=False)`, including reject-all and accept-all operating points. Every trial has equal weight.

**EER:** linear interpolation along the ROC segment crossing FPR=FNR; output is percent. An interpolated EER is generally not attainable at a single deterministic score threshold. Accordingly its `threshold` is null, with the bracket and interpolation weight reported. This differs from closest-observed-point recipes; a paper must name the convention. Tied identical scores for both classes yield 50%, independent of trial ordering.

**minDCF:** minimizes `c_miss * p_target * P_miss + c_fa * (1-p_target) * P_fa`. `p_target` is mandatory: there is no universal prior. Costs default to 1/1 and are recorded. `normalized=True` divides by `min(c_miss*p_target, c_fa*(1-p_target))`; both raw and normalized values, costs, selected threshold and error rates are returned. Tied minima choose the most restrictive threshold. Reject-all has a null threshold and an explicit `decision="reject_all"` marker. This follows the detection-cost construction in the [NIST SRE evaluation plan](https://www.nist.gov/document/nistsre10evalplan-r6pdf); it does not claim to reproduce every NIST edition's trial weighting or protocol.

minDCF is an oracle sweep over evaluation scores. It is not actual DCF at a threshold fixed on a development set, and not a calibration metric. EER/minDCF must **not** be averaged per utterance or speaker. Batch calls are rejected; call `run` once for the complete trial set. Population performance additionally requires a published trial list, enrollment rules, data separation, language/channel conditions, and any score normalization/calibration policy. The included analytical tests validate the scorer, not speaker-recognition benchmark performance.

## Reproduce the integration validation

Provision the three upstream models and prepare `st-16000`, `nst-16000`, `dt-16000`, and corresponding `*-48000` fixture directories. Each contains `farend.wav`, `microphone.wav`, `hypothesis.wav` of equal length (the recorded validation uses ten seconds). Use authentic scenario annotations. The released evidence uses AEC Challenge recordings with **unprocessed microphone passthrough**, not an AEC algorithm under test. Its 48 kHz audio was explicitly resampled from 16 kHz for interface coverage, so those scores do not establish native fullband model accuracy.

```bash
python scripts/validate_aec.py --config deployment.local.json --fixtures /audio/aec-fixtures --output aec-validation.local.json
python -m unittest discover -s tests -p test_aec_verification.py -v
```

The real inference checks compare every head with direct upstream CPU calls, compare CPU/GPU values, inspect ONNX profiling for executed CUDA kernels, repeat scores, and exercise invalid-input/hash/device controls. Pure scorer tests use known EER cases and 100 independently enumerated threshold trials for minDCF, with both raw and normalized outputs. Neural weights and private audio are not included in the package or public CI.

Absolute acceptance tolerances are 1e-6 for CPU/upstream, 1e-4 for GPU/upstream, and 1e-6 for repeated GPU/profiling-on/off comparisons. With the final deterministic/FP32 profile, the maximum recorded GPU/upstream difference was 9.54e-7 and ordinary repeats were identical. These observed values do not promise bitwise equivalence across machines.
