# Validation evidence

There are two distinct evidence layers: the **v0.2 real-model integration baseline** and **v0.3 public packaging/API checks**. Neither is a complete benchmark leaderboard reproduction.

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
