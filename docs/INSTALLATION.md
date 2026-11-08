# Installation

## Supported validation scope

| Component | Tested scope |
|---|---|
| Standard scorers and public API | Linux; Python 3.10/3.11 in the public CI matrix |
| Pretrained model integrations | Linux; Python 3.10; CPU; recorded artifacts and dependency versions |
| Workbench compatibility | Existing Windows CPython 3.10 MeetEval deployment; not all neural models on Windows |

The package declares Python >=3.10. A declared lower bound is not a claim that every dependency supports every newer Python release. Start with 3.10 or 3.11.

## Minimal and core environments

```bash
git clone https://github.com/YangXu212/SpeechMetricHub.git
cd SpeechMetricHub
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
speechmetrichub list
```

The minimal installation supports discovery and configuration inspection; scoring requires the relevant extras:

| Extra | Purpose |
|---|---|
| `transcription` | MeetEval and kaldialign |
| `quality` | PESQ, STOI/ESTOI, waveform I/O and resampling |
| `separation` | fast-bss-eval |
| `spectral` | LSD/MCD: librosa, pysptk, fastdtw; compiler may be required |
| `plcmos` | PLCMOS ONNX runtime; combine with `models` and explicitly provision official source/checkpoint |
| `diarization` | pyannote.metrics and compatible core/database versions |
| `models` | Common Torch/Transformers/audio model dependencies |
| `aesthetics`, `scoreq`, `dnsmos`, `sheet`, `speaker` | Family-specific dependencies; combine with `models` as appropriate |
| `dev` | Build, test and lint tools |

```bash
python -m pip install "numpy<2" ".[transcription,quality,separation,diarization]"
python -m pip check
```

MeetEval 0.4.3 and PESQ can require compilation. On Debian/Ubuntu, install `build-essential` and `libsndfile1` using your normal system provisioning process. See [Windows notes](../WINDOWS_BUILD.md) for Windows-specific compiler details.

## Model environments

Use a separate environment for historical model dependency stacks. For example:

```bash
python -m pip install ".[models,aesthetics]"
# or
python -m pip install ".[models,scoreq]"
```

The SCOREQ 1.0.0 profile pins ONNX Runtime 1.16.3. Do not install both `onnxruntime` and `onnxruntime-gpu` into the same environment. A CPU execution profile does not imply that the installed Torch distribution contains no CUDA libraries.

SHEET, NISQA, SpeechMOS and other source-based models also require explicitly provisioned upstream source/artifacts. See [MODELS.md](MODELS.md). Model wheels alone do not supply every source repository or checkpoint. Each family can specify a separate `python` interpreter in its configuration.

## Release wheel

Download a wheel and its checksums from [GitHub Releases](https://github.com/YangXu212/SpeechMetricHub/releases), verify SHA-256, and install the desired extras:

```bash
python -m pip install "./speechmetrichub-0.5.0-py3-none-any.whl[transcription]"
```

No PyPI publication is implied. Source installation can also be pinned to the release tag:

```bash
python -m pip install "speechmetrichub[transcription] @ git+https://github.com/YangXu212/SpeechMetricHub.git@v0.5.0"
```

## Container recipe

```bash
docker build -t speechmetrichub .
docker run --rm speechmetrichub list --category recognition
```

The Dockerfile describes a core-scoring image. It does not bundle pretrained weights. Docker runtime is outside the recorded model integration baseline; successful CI/package installation is a separate claim.

## v0.5 AEC / verification and deployment locks

See [AECMOS, ERLE, EER and minDCF profiles](AEC_VERIFICATION.md) and [locked worker deployment](DEPLOYMENT_LOCKS.md).
