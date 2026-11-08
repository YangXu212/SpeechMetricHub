# Python and command-line API

For a provisioned shared environment, use `MetricHub()` with
`SPEECHMETRICHUB_DEPLOYMENT`, or pass the lock path explicitly. It offers `run` and
`evaluate` with verified model configs loaded automatically. See the
[shared deployment examples](SHARED_DEPLOYMENT.md). Ordinary `run`/`evaluate`
remain available for callers supplying their own explicit configs.

## Discover metrics

```python
from speechmetrichub import get_metric, list_metrics

metrics = list_metrics(category="perceptual_quality", reference_kind="none")
target_speech_metrics = list_metrics(domain="tse")
spec = get_metric("scoreq_natural_ref")
```

`domain` is the historical name for task tags. Registry fields include `id`, `category`, `reference_kinds`, `domains`, `direction`, `unit`, `source`, dependencies and validation scope. Neural-model entries include a `family` and an `output` selector. An `alias_of` entry is not a distinct metric variant.

## Single metric

```python
from speechmetrichub import run
result = run("wer", reference="hello world", hypothesis="hello word")
```

Common successful fields are `metric`, `status="ok"` and a finite `value`. Additional fields preserve the upstream algorithm's useful counts/components. Units may be in `value_unit` or a legacy `unit` field; the registry's `unit` is the canonical metric output unit. Do not infer percent versus fraction from the metric name.

Text results expose `N`, `S`, `D`, `I`, `errors` and percent `value`. Model results include all raw `values`, the selected scalar, protocol, backend versions, provenance and execution settings. [result.schema.json](../speech_eval/result.schema.json) describes the common envelope; additional algorithm-specific fields are retained.

Known scoring failures return a status and null value, including `dependency_unavailable`, `invalid_input`, `timeout`, `backend_error`, `nonfinite_result` and `undefined_reference`. Invalid caller arguments can raise `ValueError`/`TypeError` before creating a result; callers should handle those errors. `evaluate_batch` catches per-record exceptions and retains them.

## Input types

| Family | Input shape / constraints |
|---|---|
| WER/CER | Text or segments containing `speaker`, `text`, optionally `start/end` |
| cp/tcp, ORC/MIMO/DI | Recording-level speaker segments; time-constrained variants require valid timestamps |
| TS-ASR | Predetermined target text/stream, never answer-guided stream selection |
| PESQ/STOI/SI-SDR | Mono arrays or files; explicit sample rate; equal length; SI-SDRi also needs `mixture` |
| BSS SDR/SIR/SAR | Equal `[sources, samples]` arrays; explicit permutation and filter settings |
| DER/JER/VAD | Activity segments, explicit `uem`, `reference_is_speech_activity=True` |
| Neural models | Local mono audio path, family configuration, appropriate reference if required |
| Correlations | >=3 paired finite subjective/predicted ratings; constant arrays are undefined |

The model deployment profile rejects silence and clips shorter than one second; it does not silently downmix stereo. Whisper's validated English profile requires clips no longer than 30 seconds. These are explicit integration-profile limits, not universal properties of the underlying methods.

## Multiple model outputs

```python
from speechmetrichub import evaluate

results = evaluate(
    ["speechbert_precision", "speechbert_recall", "speechbert_f1"],
    reference="/audio/reference.wav",
    hypothesis="/audio/prediction.wav",
    configs={"speechbert": deployment_config},
)
```

`configs` maps model family names to configurations. The model runs once per family in this call and each requested head is selected from its output. Non-model arguments such as `sample_rate` are passed to non-model adapters. Different recordings currently launch separate workers.

## Corpus aggregation

```python
from speechmetrichub import evaluate_batch

report = evaluate_batch("wer", records=[
    {"id": "a", "inputs": {"reference": "one", "hypothesis": ""}},
    {"id": "b", "inputs": {"reference": "one two three", "hypothesis": "one two three"}},
])
assert report["value"] == 25.0
```

`records` require unique IDs. Shared keyword arguments are merged with each record's `inputs`, with the record taking precedence. Reports include `expected`, `scored`, `coverage`, `complete`, `value`, `valid_subset_value`, `aggregation`, `counts` and every record result.

Different protocol/backend fingerprints are rejected. Model artifact hashes participate in that fingerprint; per-input hashes do not. For incomplete coverage, `value` is null. Never relabel the valid-subset value as a complete-set score. Rating correlations are dataset-level operations and cannot be averaged through this batch API.

## CLI

```text
speechmetrichub list [--category NAME] [--task TAG] [--reference-kind KIND]
speechmetrichub run METRIC --input INPUT.json [--output RESULT.json]
speechmetrichub batch METRIC --input BATCH.json [--output REPORT.json]
speechmetrichub evaluate --input MULTI.json [--output RESULTS.json]
speechmetrichub doctor [--config DEPLOYMENT.json] [--verify-hashes]
```

Input JSON contains the corresponding Python keyword arguments. Success returns exit code 0. A returned scoring failure or incomplete batch returns 2. Invalid arguments/uncaught exceptions may return the interpreter's error exit code. `doctor` inspects the current interpreter and local artifact files; it does not validate another configured interpreter by executing it, and does not run inference.

## Custom metrics

```python
from speechmetrichub import register

def my_metric(*, reference, hypothesis):
    return {"metric": "my_metric", "status": "ok", "value": 0.0}

register("my_metric", my_metric,
         domains=["research"], category="custom",
         reference_kinds=["transcript"], direction="lower_is_better",
         unit="ratio", description="Replace with a precise definition",
         source="https://example.org/original-method")
```

Registration is process-local and rejects duplicate names. A custom registration is not marked runtime-validated. See [EXTENDING.md](EXTENDING.md) for the integration standard.

## v0.5 AEC / verification and deployment locks

See [AECMOS, ERLE, EER and minDCF profiles](AEC_VERIFICATION.md) and [locked worker deployment](DEPLOYMENT_LOCKS.md).
