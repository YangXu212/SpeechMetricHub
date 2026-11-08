"""Execute v0.4 profiles and changed legacy model paths against local fixtures.

No downloads. Example: python scripts/validate_expansion.py --config deployment.json
--fixtures /audio/fixtures --output results.json. Fixtures: ref/noisy/aux/rate24/
short/silent/stereo.wav (the first three must be real speech).
"""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from speechmetrichub import evaluate, run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--only", nargs="+", help="Re-run named model groups in an existing report")
    args = parser.parse_args()
    configs = json.loads(Path(args.config).read_text())
    f = Path(args.fixtures)
    groups = [
        ["speechbert_mhubert_precision", "speechbert_mhubert_recall", "speechbert_mhubert_f1"],
        ["speaker_similarity_wavlm"],
        ["plcmos_v2"],
        ["plcmos_v2_val"],
        ["phoneme_similarity", "lps_phone"],
        ["speechbert_precision", "speechbert_recall", "speechbert_f1"],
    ]
    report = {"release": "0.4.0", "model_cases": {}, "spectral_cases": {}}
    if args.only:
        report = json.loads(Path(args.output).read_text())
        groups = [g for g in groups if g[0] in args.only]
        if not groups:
            parser.error("No matching model group")
    failures = []

    def save():
        Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")

    for group in groups:
        name = group[0]
        cases = {}
        for case, hyp, ref in [
            ("degraded", "noisy.wav", "ref.wav"),
            ("identity", "ref.wav", "ref.wav"),
            ("nonmatching", "aux.wav", "ref.wav"),
            ("resampled", "rate24.wav", "ref.wav"),
            ("short", "short.wav", "ref.wav"),
            ("silent", "silent.wav", "ref.wav"),
            ("stereo", "stereo.wav", "ref.wav"),
            ("missing", "missing.wav", "ref.wav"),
        ]:
            result = evaluate(
                group, hypothesis=str(f / hyp), reference=str(f / ref), configs=configs
            )
            cases[case] = result
            expected_ok = case in ("degraded", "identity", "nonmatching", "resampled")
            for id, row in result.items():
                if (row.get("status") == "ok") != expected_ok:
                    failures.append(f"{id}/{case}: {row.get('status')} {row.get('reason', '')}")
            print(
                name,
                case,
                {k: (v.get("status"), v.get("value")) for k, v in result.items()},
                flush=True,
            )
            report["model_cases"][name] = cases
            save()
    for name in () if args.only else ("lsd_urgent", "lsd_db", "mcd_urgent", "mcd_dtw_c1"):
        cases = {}
        for case, hyp in [
            ("degraded", "noisy.wav"),
            ("identity", "ref.wav"),
            ("short", "short.wav"),
            ("silent", "silent.wav"),
            ("stereo", "stereo.wav"),
            ("missing", "missing.wav"),
            ("wrong_rate", "rate24.wav"),
        ]:
            result = run(
                name, reference=str(f / "ref.wav"), hypothesis=str(f / hyp), sample_rate=16000
            )
            cases[case] = result
            if (result.get("status") == "ok") != (case in ("degraded", "identity")):
                failures.append(f"{name}/{case}: {result}")
        report["spectral_cases"][name] = cases
        save()
        print(name, {k: (v["status"], v["value"]) for k, v in cases.items()}, flush=True)
    failures = []
    for cases in report["model_cases"].values():
        for case, rows in cases.items():
            expected_ok = case in ("degraded", "identity", "nonmatching", "resampled")
            for name, result in rows.items():
                if (result.get("status") == "ok") != expected_ok:
                    failures.append(f"{name}/{case}: {result.get('status')}")
    for name, cases in report["spectral_cases"].items():
        for case, result in cases.items():
            if (result.get("status") == "ok") != (case in ("degraded", "identity")):
                failures.append(f"{name}/{case}: {result.get('status')}")
    report["failures"] = failures
    save()
    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
