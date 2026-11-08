# Versioned worker deployments

The [v0.6 shared profile](SHARED_DEPLOYMENT.md) supplies a tested full environment for all metric families, with Torch 2.8 and CPU ONNX Runtime 1.16.3. Use its pinned requirements for that profile; installing arbitrary combinations of extras is not equivalent. The separate v0.5 AECMOS GPU profile below remains available. Core imports stay lightweight. CPU and GPU ONNX Runtime distributions install the same Python module: install exactly one in a worker.

## Provision and validate

1. Create a clean Python 3.10 environment and install this release with `.[aecmos-cpu,verification,echo]` or `.[aecmos-gpu,verification,echo]`. Match NVIDIA libraries to the selected ONNX build using its [official compatibility table](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html). GPU libraries and driver support are deployment prerequisites, not proof of inference support.
2. Download the public `speechmos==0.0.1.1` wheel without dependencies and unpack it into your artifact directory. Supply its original `speechmos/aecmos.py` and matching `aecmos_models/*.onnx`. Do not install unrelated scorers into the worker just to extract weights. SHA-256 checks enforce the exact source/model identities.
3. Fill a local config mapping family names to paths. See [the example](../examples/aec_deployment.json). Paths in the example are placeholders; downloaded code and checkpoints are trusted local artifacts.
4. Run `python -m pip check`, inspect `speechmetrichub doctor --config deployment.local.json --verify-hashes`, and run actual scoring/validation on the intended device. `doctor` is inspection, not inference validation.
5. Create the lock **after** validation and installation are complete. Preserve the dependency snapshot and runtime report next to it.

AECMOS pins **ONNX Runtime 1.16.3**. In direct checks, the original scenarioless checkpoint failed newer 1.18.1, 1.19.2 and 1.20.0 shape inference (`Concat_49`); neither disabling optimization nor clearing shape metadata resolved it. The published model is not rewritten. The adapter enforces the tested runtime version. Runtime 1.16.3 has no public `use_tf32` switch, so the isolated worker sets NVIDIA's `NVIDIA_TF32_OVERRIDE=0`. It also uses deterministic compute, `cudnn_conv_algo_search=DEFAULT` and `CUBLAS_WORKSPACE_CONFIG=:4096:8`. These settings and the measured CPU/GPU parity are recorded. See [NVIDIA's TF32 control documentation](https://developer.nvidia.com/blog/accelerating-ai-training-with-tf32-tensor-cores/). No cross-hardware bitwise guarantee is implied.

For a self-contained Linux NVIDIA user-space stack, install `.[aecmos-gpu,cuda11-libs,verification,echo]`. The optional `cuda11-libs` group pins CUDA 11/cuDNN 8 libraries in this environment. The model subprocess discovers these distributions and prepends their library directories; it does not require importing PyTorch or changing a shared environment. The NVIDIA driver still comes from the host. A custom `python` worker needs its own matching library launcher. Windows GPU and Docker runtime have not been validated for these profiles.

```bash
python -m pip freeze > requirements.deployed.txt
speechmetrichub lock --config deployment.local.json --output deployment.locked.json
speechmetrichub verify --deployment deployment.locked.json
speechmetrichub evaluate --deployment deployment.locked.json --input examples/aec_request.json --output scores.json
speechmetrichub run eer --input examples/verification_trials.json
```

The lock contains the package version, Python patch version, OS/architecture, installed distribution versions, hashes of library source/registry files, artifact paths and hashes, and model settings. `load_deployment(path)` verifies these before returning configs. `families=[...]` scopes artifact checks to those families while retaining the full environment check. Distribution discovery uses installed site-package locations, avoiding vendored packages added to `sys.path` by optional imports. CLI `run`, `evaluate`, and `batch` accept `--deployment` or `SPEECHMETRICHUB_DEPLOYMENT`; request data cannot override locked configs. Missing configured families are rejected. Locks use absolute local paths and are **not portable manifests to copy unchanged across machines**. Shared mounts may reuse a lock only when those paths and the runtime match and cross-host scoring has been validated. Keep local locks out of Git.

Alternate worker interpreters remain available in ordinary configs through `python`, but a strict lock must be created and used inside the actual worker interpreter. This avoids claiming that the caller's dependencies describe another environment. For multiple incompatible stacks, keep one lock and command entry point per environment.

## Runtime behavior and failure handling

- AECMOS validates native rate, mono channels, duration, amplitude, lengths and scenario. It will not silently resample or truncate.
- `device="cuda:N"` selects a physical CUDA index and isolates the subprocess. If CUDA cannot initialize, the request fails instead of returning CPU-only scores. ONNX may still place supporting operators on CPU; actual CUDA execution is checked in the integration profile.
- One worker process serves one model-family call and exits. Multiple requested output heads share that call. No desktop terminal or persistent service needs to remain open. This release is not a persistent HTTP server or high-throughput model pool.
- Timeout, missing dependency, invalid input and backend failure remain distinct statuses. JSON disallows NaN/Infinity. Inspect `status`, not just the numeric value.
- CLI scoring/verification failures return exit code 2. An incomplete batch or a complete batch with an undefined numeric result also returns 2. Invalid request JSON is reported as structured JSON on standard output.
- Locked mode checks integrity, not scientific suitability, checkpoint safety, native driver hashes, hardware equivalence, or all runtime system libraries. Retain GPU/driver/provider profiling evidence; do not describe `verify` alone as a deployment acceptance test.

The manifest covers the known artifact fields: checkpoint, source_dir, source_file, model_dir, config_file, ssl_checkpoint, primary_model, p808_model and binary. Directory fingerprints follow the worker's supported code/model/config extensions and exclude caches and `.git`; they are not complete filesystem snapshots. Existing `expected_hashes` constraints must already match before a new lock can be created.

Upgrading dependencies or editing the library makes an old lock fail. Revalidate intentionally before replacing it. Hashing large model directories has a cost; load the lock once per Python evaluation session and retain the returned immutable-by-convention config rather than repeatedly loading it inside an utterance loop.
