# One environment, shared across a Linux cluster

The v0.6 profile starts from a **copy** of a working Torch 2.8 environment and pins
the resulting full Python package inventory in [requirements.txt](../requirements.txt).
It targets **Linux x86_64, CPython 3.10.19, Torch 2.8.0+cu128**. It includes inherited
training and development packages; it is intentionally not a minimal install.
Core-only installations and their Python 3.10/3.11 CI remain supported separately.

The [per-interface report](../validation/shared-environment-v0.6.json) records actual
independent calls, including every output head and compatibility alias. Successful
fixture execution establishes interface availability in this profile, not model
accuracy, throughput, or compatibility with arbitrary future package upgrades.

## Compatibility decisions

| Component | Shared profile | Reason |
|---|---|---|
| Torch / torchaudio / torchvision | 2.8.0+cu128 / 2.8.0+cu128 / 0.23.0+cu128 | Preserve the familiar training stack |
| NumPy | 1.23.5 | Satisfy ESPnet 202412 and exercise all scorers together |
| SciPy / librosa | 1.13.1 / 0.9.2 | Recorded upstream audio stack |
| ONNX Runtime | **CPU 1.16.3 only** | SCOREQ requirement and original AECMOS graph compatibility |
| scikit-learn | 1.5.2 | Match the recorded verification profile |
| setuptools | 73.0.1 at runtime | ESPnet requires a version below 74 |
| MeetEval / pyannote.metrics | 0.4.3 / 3.2.1 | Fixed transcription/diarization implementations |

CPU and GPU ONNX Runtime distributions overlap on the same import namespace.
The source environment contained both; the copy removes the GPU distribution and
reinstalls CPU 1.16.3. **Torch CUDA remains installed.** This is an all-metric CPU
profile with optional Torch CUDA execution, not an all-metric ONNX GPU profile.
For AECMOS GPU use the separately validated [v0.5 profile](DEPLOYMENT_LOCKS.md).

The package build uses isolated setuptools >=77; this does not upgrade runtime
setuptools 73.0.1. Do not disable build isolation when building this profile.

## Reproduce the environment

For an existing Conda baseline, clone it without modifying the source:

```bash
conda create --name speechmetrichub --clone torch28 --copy
conda activate speechmetrichub
python -m pip uninstall -y onnxruntime-gpu
python -m pip install --force-reinstall --no-deps onnxruntime==1.16.3
python -m pip install -r requirements.txt
python -m pip install --no-deps .
python -m pip check
```

For a new installation, create Python 3.10.19 first and install the requirements
and package. The published runtime acceptance comes from the cloned environment;
it is not a claim that every inherited source distribution was rebuilt from scratch.
The requirements use the official CUDA 12.8 PyTorch wheel index. The NVIDIA driver
is a host prerequisite for CUDA, not a pip dependency.

System prerequisites include a C/C++ compiler for source builds, libsndfile, and
the binaries required by selected upstream models. ViSQOL's executable and models,
NISQA/SpeechMOS/SHEET/DiscreteSpeechMetrics source trees, and all neural checkpoints
are **separate provisioned artifacts**. Installing requirements alone does not
download them. Follow [model configuration](MODELS.md), use the recorded official
revisions/hashes, and obey each upstream license. Private audio and model weights
are not included in this repository.

## Provision a shared entry point

Use a shared home directory only after verifying that the participating machines
mount the same files. An identical username alone does not establish shared storage.
Keep artifacts under the deployment root and configure CPU by default on a shared
cluster. Set `device="cuda:N"` only for a reserved or otherwise available GPU.

```bash
mkdir -p "$HOME/SpeechMetricHub"
# Prepare deployment.local.json with the 23 model-family configurations.
python scripts/validate_all.py --config deployment.local.json \
  --fixtures /path/to/fixtures --output runtime.local.json
python scripts/create_shared_deployment.py --root "$HOME/SpeechMetricHub" \
  --config deployment.local.json
"$HOME/SpeechMetricHub/bin/smh" verify \
  --deployment "$HOME/SpeechMetricHub/deployment.locked.json"
```

The setup script creates a local lock, `bin/smh`, and `activate.sh`. It does not
modify shell startup files, install packages, or download models. The lock must be
created **after the final wheel is installed**: checkout and installed-wheel package
inventories can differ. The supplied config must not point to alternate Python
interpreters in a single-environment acceptance run.

### From any experiment environment

Call the absolute entry point; your experiment's Python environment stays active:

```bash
"$HOME/SpeechMetricHub/bin/smh" run wer --input request.json --output result.json
"$HOME/SpeechMetricHub/bin/smh" evaluate --input audio-request.json --output scores.json
```

For example, `audio-request.json` can contain:

```json
{
  "metrics": ["nisqa_mos", "nisqa_noi", "nisqa_dis", "nisqa_col", "nisqa_loud"],
  "hypothesis": "/absolute/path/to/audio.wav"
}
```

Multiple outputs of one model share a forward pass in `evaluate`. AECMOS instead
requires far-end, microphone, enhanced audio and the declared scenario; EER/minDCF
require trial scores/labels. A common API does not make different metrics' inputs
interchangeable. Consult each metric card before building request data.

### Python in the evaluation environment

```bash
source "$HOME/SpeechMetricHub/activate.sh"
python
```

```python
from speechmetrichub import MetricHub

hub = MetricHub()  # Uses SPEECHMETRICHUB_DEPLOYMENT set by activate.sh.
score = hub.run("wer", reference="hello world", hypothesis="hello word")
scores = hub.evaluate(
    ["audiobox_aesthetics_ce", "audiobox_aesthetics_cu",
     "audiobox_aesthetics_pc", "audiobox_aesthetics_pq"],
    hypothesis="/absolute/path/to/audio.wav",
)
```

You can pass `MetricHub("/absolute/path/to/deployment.locked.json")` explicitly.
The hub checks the installed environment and library on construction, then verifies
the requested family's artifacts on first use. Workers still enforce expected
artifact hashes. CLI scoring verifies the requested families; `verify` checks all
families. Stateless WER/EER calls do not read unrelated multi-gigabyte checkpoints.
Config overrides are rejected in locked mode. Recreate the hub after intentional
environment changes, rerun inference acceptance, and regenerate the lock.

Each model call uses a subprocess and exits. No PowerShell terminal, background
server, or GPU-resident daemon is required. Cold loading and artifact hashing cost
time: this entry point is convenient, not a promise of low-latency model serving.

## Acceptance and maintenance

Run `pip check`, the semantic/API regression suite, all 89 registry IDs through
`scripts/validate_all.py`, installed-wheel tests outside the checkout, and a real
cross-host CLI call before treating a deployment as ready. Inspect `status` and
finite values, not just whether a process launched. Preserve fixture hashes,
package versions, source/model fingerprints and failures in the report.

The validation fixtures include real speech with controlled degradation, analytical
transcript/trial cases, and explicit AEC scenario inputs. Whisper's convenience
fixture transcript is not a matched ground-truth transcript, so its WER is not a
quality benchmark. The six AEC outputs are also compared against the earlier
upstream-validated CPU results for the same fixture bytes.

The initial baseline environment is never changed. Updates belong in a new copy
or a deliberately versioned evaluation deployment. Shared storage permits reuse;
different host libraries, CPU instructions or GPU drivers can still affect behavior.
Only the hosts and devices recorded in the evidence are claimed as tested.

## v0.7 pitch extension

The v0.7 environment adds praat-parselmouth==0.4.7; WORLD was already present. The five new [pitch interfaces](PITCH.md) are CPU-only and need no weights. Their [separate validation report](../validation/pitch-v0.7.json) complements the unchanged historical v0.6 acceptance evidence. Existing deployment locks must be regenerated after the package/dependency update; do not reuse a v0.6 lock with changed code.
