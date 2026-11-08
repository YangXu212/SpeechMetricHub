# Validation evidence

## v0.6 shared environment

The [single-environment report](shared-environment-v0.6.json) records independent calls to every registry ID, including all model output heads and aliases. The environment is a dedicated copy of a Torch 2.8 baseline with a pinned [full package inventory](../requirements.txt). It retains CUDA 12.8 Torch but deliberately uses CPU ONNX Runtime 1.16.3. All-metric acceptance uses CPU; optional GPU and cross-host checks are separately identified in the report.

This release adds 57 semantic/API regression checks in total, requirements resolution and `pip check`, installed-wheel execution, shared CLI/API checks, and same-fixture comparison of the six AEC heads to v0.5's upstream-validated CPU values. The old baseline environment is unchanged. See [reproduction and limits](../docs/SHARED_DEPLOYMENT.md). Successful integration fixtures are not benchmark-quality scores or an assurance of compatibility with future upgrades.

## v0.5 AEC / verification release evidence

The installed wheel passed **54 semantic/API regression tests** outside the source checkout. All **16 deployment checks** passed, including locked CLI inference for every new model family, all three stateless scorer CLIs, dependency checks and refusal of changed artifacts/environments or request-level config overrides. The [deployment report](deployment-v0.5.json) includes the exact package inventory and library fingerprint.

[Detailed report](aec-verification-v0.5.json) adds nine interfaces without replacing older evidence. All **72 real AEC checks passed**: six AECMOS heads across three scenarios, direct upstream CPU parity, CPU/GPU comparison, actual CUDA-kernel profiling, repeated execution, input/model/hash/device rejection controls, silent enhanced-output handling and real-waveform ERLE checks. Maximum observed GPU/upstream CPU difference was **9.54e-7**; ordinary repeated values were identical in the recorded checks. These are integration fixtures, not model-quality benchmark results.

The runtime was a clean Python 3.10 environment on an RTX 3090, ONNX Runtime GPU 1.16.3, with its own pinned CUDA 11/cuDNN 8 user-space packages. Original weights are unchanged. Newer tested ONNX versions fail to load the original scenarioless graph. The profile fixes deterministic execution, convolution algorithm selection, cuBLAS workspace and disables TF32 in its isolated worker.

EER is checked against known perfect/reversed/tied operating points and direction/tie-order invariance. minDCF is checked against independently enumerated thresholds on 100 seeded random tied-score trial lists, in both raw and normalized modes. The fixtures validate scoring semantics; they do not estimate a population EER or an operational decision threshold.

The real AEC inputs are explicit first-ten-second windows from three AEC Challenge scenarios, with microphone passthrough as the hypothesis. Source recordings can differ in total length; no hidden crop occurs inside the adapter. The 48k fixtures are deliberately resampled from 16k for interface validation and are not native fullband benchmark evidence. Private audio is not redistributed. See [protocols and reproduction](../docs/AEC_VERIFICATION.md) and [deployment locks](../docs/DEPLOYMENT_LOCKS.md).


## v0.4 expansion

The [v0.4 evidence matrix](expansion-v0.4.json) records **11 new interfaces**, bringing the registry to **80 IDs / 75 canonical variants**. It preserves the older baseline below rather than overwriting its history.

| Check | Recorded outcome |
|---|---|
| Semantic/API regression suite | 39 tests passed |
| Real model execution | 48 family/case executions, producing 88 interface/case results across new and affected legacy paths |
| Spectral profiles | 28 interface/case results across four profiles |
| Independent parity / analytic checks | 14 passed, covering all 11 new interfaces and three existing SBS heads |
| Additional controls | 11 passed: fixed-seed repeatability, invalid seed/repetition settings, speaker positive/negative, missing references and artifact mismatch |
| Legacy compatibility | Existing HuBERT SBS P/R/F1 and IPA-character similarity exactly match the recorded v0.2 degraded-fixture values |

Successful and intentionally invalid cases are distinguished in the matrix. Model cases include real degraded speech, identity, different content, explicit resampling, and short/silent/stereo/missing files. The different-content fixture is from the same speaker; a separate speaker-control fixture supplies the impostor. Observed WavLM cosine was 0.9406 for another utterance by the same speaker and 0.4850 for the other speaker. This single control does not establish a recognition threshold or population EER.

Independent checks use public upstream calls or a separately specified mathematical reference: current URGENT phone-token LPS, direct encoder features and cosine reductions for SBS/WavLM, Microsoft SpeechMOS PLCMOS, public URGENT LSD/MCD, and a known 6.0205999 dB half-amplitude fixture for `lsd_db`. Sources and model/input SHA-256 identities are recorded. Upstream tolerance is 1e-5 for neural features and 1e-7 for deterministic PLCMOS/spectral comparisons.

Model tests used a dedicated Linux/Python 3.10 CPU environment with two threads and inherited dependencies. This is not a fresh installation of every model stack. All historical heavyweight families were not rerun: changed legacy paths and every newly admitted ID were exercised. Public CI separately tests fresh core/spectral installs on Python 3.10 and 3.11; it does not download neural weights.

To reproduce with your provisioned artifacts and fixture directory:

```bash
python scripts/validate_expansion.py --config deployment.local.json --fixtures /audio/fixtures --output runtime.local.json
python scripts/validate_expansion_parity.py --config deployment.local.json --fixtures /audio/fixtures --upstream /opt/public-reference-scripts --results runtime.local.json --output parity.local.json
python scripts/validate_expansion_controls.py --config deployment.local.json --fixtures /audio/fixtures --output controls.local.json
```

The fixture directory contains `ref.wav`, `noisy.wav`, `aux.wav` (same speaker/different text), `impostor.wav` (different speaker), `rate24.wav` (reference resampled to 24 kHz), `short.wav`, `silent.wav`, and `stereo.wav`. `missing.wav` must not exist. The parity script requires `urgent_lps.py`, `urgent_intrusive.py` and `mcd_utils.py` from the public URLs in the JSON report. Read [exact profiles](../docs/EXPANSION_PROFILES.md) before comparing results.

The inherited evidence has two layers: the **v0.2 real-model integration baseline** and **v0.3 public packaging/API checks**. Neither is a complete benchmark leaderboard reproduction.

## Real-model integration baseline

[summary.json](summary.json) retains the original v0.2 report:

| Check | Recorded outcome |
|---|---|
| Registered interfaces | 69 passed: 64 canonical variants + 5 migration aliases |
| Standard scorer interfaces | 33 actual calls with upstream comparisons or analytic fixtures |
| Neural-model families | 16, exercised on real LibriMix speech and controlled noise |
| Invalid model inputs | 64 family/case combinations: short, stereo, silent, missing file |
| Independent model parity | 8 families: AE, four SCOREQ modes, NISQA, UTMOS, DNSMOS; absolute error <1e-5 |
| Identity properties | 6 outputs: speaker/IPA similarity, three SpeechBERTScore heads, natural-reference SCOREQ |
| Baseline semantic tests | 29 passed |
| Fresh core installation | Python 3.10; dependency check, tests and CLI passed without inheriting training packages |

Model execution used Linux x86_64 / Python 3.10 / CPU with two threads. The model environment reused installed dependencies through a dedicated overlay; it was not a completely fresh installation of all model stacks. [environment.json](environment.json) records package versions, official source commits and 25 artifact identities. No weights or private recordings are distributed here.

The matrix distinguishes direct upstream comparisons from analytic fixtures and records per-metric outputs and input hashes. Learned scores are predictions, not human listening-study MOS. The Whisper runtime fixture tests the interface and count accounting; it is not a ground-truth ASR benchmark result.

## Public release checks

The v0.3 release preserves the underlying scorer implementation while adding a public namespace, compatibility tests and packaging/documentation. The [CI workflow](https://github.com/YangXu212/SpeechMetricHub/actions/workflows/ci.yml) runs:

- Static checks and consistent formatting.
- Standard scorer, semantic, aggregation and public API tests.
- Local documentation links, every metric card, SVG and package metadata checks.
- Wheel/source builds and an installed-wheel smoke test outside the checkout.
- Linux/Python 3.10 and 3.11 jobs.

CI status is reported by the actual workflow, not a hardcoded passing badge. Heavy model inference is not part of these public jobs. The historical report's statement that CI was not executed refers to its original v0.2 run, not the live v0.3 workflow.

## Repeat the checks

```bash
python -m pip install "numpy<2" ".[transcription,quality,separation,diarization,dev]"
python -m unittest discover -s tests -v
python scripts/check_docs.py
python -m build
python scripts/validate_models.py --help
```

The model harness requires your local deployment configuration, predicted/clean/nonmatching-reference audio and reference text. It saves every declared output and returns a failure exit code if an interface fails. Keep the resulting report for the actual machine/configuration you use.

## Not claimed

No exhaustive GPU equivalence, all-Windows-model support, all languages, all SHEET checkpoints, all distortion types, Docker runtime validation or full-test-set benchmark reproduction is implied. Interface validity and domain validity are different questions.
