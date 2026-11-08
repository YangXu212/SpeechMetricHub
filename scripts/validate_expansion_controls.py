"""Recheck seed, model identity, input and speaker controls using local artifacts."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from speechmetrichub import run

parser = argparse.ArgumentParser()
for name in ("config", "fixtures", "output"):
    parser.add_argument("--" + name, required=True)
args = parser.parse_args()
c = json.loads(Path(args.config).read_text())
f = Path(args.fixtures)
rows = {}


def check(name, result, passed):
    rows[name] = {"passed": bool(passed), "result": result}
    print(name, passed, flush=True)
    Path(args.output).write_text(json.dumps(rows, indent=2) + "\n")


for family in ["plcmos_v2", "plcmos_v2_val"]:
    a = run(family, hypothesis=str(f / "noisy.wav"), config=c[family])
    b = run(family, hypothesis=str(f / "noisy.wav"), config=c[family])
    check(
        family + "_repeat",
        {"a": a["value"], "b": b["value"]},
        a["status"] == b["status"] == "ok" and a["value"] == b["value"],
    )
    for key, value in [("seed", -1), ("embed_rounds", 0)]:
        bad = run(family, hypothesis=str(f / "noisy.wav"), config={**c[family], key: value})
        check(family + "_" + key, {"status": bad["status"]}, bad["status"] == "invalid_input")
spk = run(
    "speaker_similarity_wavlm",
    reference=str(f / "ref.wav"),
    hypothesis=str(f / "impostor.wav"),
    config=c["speaker_similarity_wavlm"],
)
same = run(
    "speaker_similarity_wavlm",
    reference=str(f / "ref.wav"),
    hypothesis=str(f / "aux.wav"),
    config=c["speaker_similarity_wavlm"],
)
check(
    "speaker_positive_negative",
    {"same_speaker_different_text": same["value"], "different_speaker": spk["value"]},
    same["status"] == spk["status"] == "ok" and same["value"] > spk["value"],
)
for family, id in [
    ("speechbert_mhubert", "speechbert_mhubert_f1"),
    ("speaker_similarity_wavlm", "speaker_similarity_wavlm"),
    ("phoneme_similarity", "lps_phone"),
]:
    out = run(id, reference=None, hypothesis=str(f / "ref.wav"), config=c[family])
    check(id + "_missing_reference", {"status": out["status"]}, out["status"] == "invalid_input")
out = run(
    "plcmos_v2",
    hypothesis=str(f / "ref.wav"),
    config={**c["plcmos_v2"], "expected_hashes": {"checkpoint": "0" * 64}},
)
check("artifact_mismatch", {"status": out["status"]}, out["status"] == "invalid_input")
if not all(x["passed"] for x in rows.values()):
    raise SystemExit("Controls failed")
