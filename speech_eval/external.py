"""Opt-in bridge to existing SCP-based research scripts, isolated per run.

Does not copy colleagues' code, download weights, pick a GPU, or launch remote jobs.
Caller explicitly supplies the executable, script, arguments and model provenance.
"""

import hashlib
import json
import csv
from pathlib import Path
import subprocess
import tempfile


def scp_metric(*, metric, records, config, work_dir):
    required = ["python", "script", "output_stem", "arguments", "model_provenance"]
    if any(k not in config for k in required):
        raise ValueError(f"External config requires {required}")
    if metric in ["whisper_wer", "whisper_dwer"] and not config.get("counts_csv"):
        raise ValueError(
            "Whisper WER requires counts_csv for micro aggregation; SCP rates alone are insufficient"
        )
    provenance_model = config["model_provenance"]
    if not isinstance(provenance_model, dict) or not any(
        provenance_model.get(k) for k in ["checkpoint_sha256", "revision", "implementation_sha256"]
    ):
        raise ValueError(
            "Pin checkpoint_sha256, revision or implementation_sha256 in model_provenance"
        )
    script = Path(config["script"]).resolve()
    if not script.is_file():
        return {
            "metric": metric,
            "status": "dependency_unavailable",
            "value": None,
            "reason": f"Script absent: {script}",
        }
    records = list(records)
    ids = [str(r["id"]) for r in records]
    if len(set(ids)) != len(ids) or any(not x or any(c.isspace() for c in x) for x in ids):
        raise ValueError("Unique, nonempty, whitespace-free record IDs required")
    root = Path(work_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=metric + "-", dir=root))
    replacements = {"output_dir": str(run_dir / "metrics")}
    for side in ["hypothesis", "reference", "mixture"]:
        path = run_dir / (side + ".scp")
        lines = []
        for r in records:
            if side not in r:
                continue
            audio = Path(r[side]).resolve()
            if not audio.is_file() or any(c.isspace() for c in str(audio)):
                raise ValueError("SCP bridge requires existing paths without whitespace")
            lines.append(f"{r['id']} {audio}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        replacements[side + "_scp"] = str(path)
    args = [str(a).format_map(replacements) for a in config["arguments"]]
    command = [str(config["python"]), str(script), *args]
    provenance = {
        "metric": metric,
        "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "config": config,
        "command": command,
        "records": records,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        with (run_dir / "stdout.log").open("w", encoding="utf-8") as log:
            done = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=config.get("timeout", 3600),
                cwd=run_dir,
                shell=False,
            )
        if done.returncode:
            return {
                "metric": metric,
                "status": "backend_error",
                "value": None,
                "run_dir": str(run_dir),
                "returncode": done.returncode,
            }
    except subprocess.TimeoutExpired:
        return {"metric": metric, "status": "timeout", "value": None, "run_dir": str(run_dir)}
    except OSError as exc:
        return {
            "metric": metric,
            "status": "backend_error",
            "value": None,
            "run_dir": str(run_dir),
            "reason": str(exc),
        }
    values = {}
    duplicates = []
    for path in sorted((run_dir / "metrics").glob(config["output_stem"] + "*.scp")):
        for line in path.read_text().splitlines():
            uid, value = line.split(maxsplit=1)
            if uid in values:
                duplicates.append(uid)
            try:
                values[uid] = float(value)
            except ValueError:
                values[uid] = None
    import math

    rows = [
        {
            "id": uid,
            "status": "ok"
            if uid in values and values[uid] is not None and math.isfinite(values[uid])
            else "missing_or_invalid",
            "value": values[uid]
            if uid in values and values[uid] is not None and math.isfinite(values[uid])
            else None,
        }
        for uid in ids
    ]
    for row in rows:
        if row["id"] in duplicates:
            row.update(status="duplicate_output", value=None)
    valid = [r["value"] for r in rows if r["status"] == "ok"]
    complete = (
        bool(rows)
        and len(valid) == len(rows)
        and not duplicates
        and not set(values).difference(ids)
    )
    subset = sum(valid) / len(valid) if valid else None
    aggregation = "utterance_macro"
    totals = None
    if config.get("counts_csv"):
        counts_path = run_dir / "metrics" / config["counts_csv"]
        counts = {}
        count_duplicates = set()
        if counts_path.is_file():
            with counts_path.open(newline="", encoding="utf-8") as stream:
                for record in csv.DictReader(stream):
                    uid = record["key"]
                    if uid in counts:
                        count_duplicates.add(uid)
                    counts[uid] = record
        for row in rows:
            record = counts.get(row["id"])
            try:
                ct = {k: int(record[k]) for k in ["N", "S", "D", "I"]}
                if (
                    record["status"] != "ok"
                    or any(v < 0 for v in ct.values())
                    or row["id"] in count_duplicates
                ):
                    raise ValueError("invalid counts")
                row["counts"] = ct
                if row["status"] == "ok":
                    row["value"] = (
                        100 * (ct["S"] + ct["D"] + ct["I"]) / ct["N"] if ct["N"] else None
                    )
            except (TypeError, KeyError, ValueError):
                row.update(status="missing_or_invalid_counts", value=None)
        valid_rows = [r for r in rows if r["status"] == "ok"]
        valid = [r["value"] for r in valid_rows]
        complete = (
            bool(rows)
            and len(valid_rows) == len(rows)
            and not count_duplicates
            and not set(counts).difference(ids)
            and complete
        )
        totals = {k: sum(r["counts"][k] for r in valid_rows) for k in ["N", "S", "D", "I"]}
        subset = (
            100 * (totals["S"] + totals["D"] + totals["I"]) / totals["N"] if totals["N"] else None
        )
        aggregation = "micro_errors_over_reference_words_percent"
    return {
        "metric": metric,
        "status": "ok" if complete else "incomplete",
        "value": subset if complete else None,
        "valid_subset_value": subset,
        "aggregation": aggregation,
        "counts": totals,
        "coverage": len(valid) / len(rows) if rows else None,
        "rows": rows,
        "duplicates": duplicates,
        "unexpected_ids": sorted(set(values).difference(ids)),
        "run_dir": str(run_dir),
        "provenance": provenance,
    }
