"""Batch accounting for optional metric APIs. Failures never disappear."""

import json
import math
from .registry import run, get_metric


def evaluate_batch(metric, records, **shared):
    spec = get_metric(metric)
    if spec.get("category") == "rating_agreement":
        raise ValueError("Correlation is a dataset-level metric: call run with all paired ratings")
    records = list(records)
    ids = [r["id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate recording IDs")
    rows = []
    for record in records:
        try:
            result = run(metric, **{**shared, **record["inputs"]})
        except Exception as exc:
            result = {
                "metric": metric,
                "status": "error",
                "value": None,
                "reason": f"{type(exc).__name__}: {exc}",
            }
        rows.append({"id": record["id"], "result": result})
    text_metric = spec.get("category") == "recognition"
    good = [
        r["result"]
        for r in rows
        if r["result"]["status"] == "ok"
        or (text_metric and r["result"]["status"] == "undefined_reference")
    ]

    def comparable_protocol(v):
        protocol = dict(v.get("protocol") or {})
        # UEM varies by recording; its presence remains mandatory, collar/overlap must agree.
        if metric in ("der", "jer") or metric.startswith("vad_"):
            protocol.pop("uem", None)
        return protocol

    fingerprints = {
        json.dumps(
            {
                "backend": v.get("backend"),
                "protocol": comparable_protocol(v),
                "unit": v.get("value_unit", v.get("unit")),
                "collar": v.get("collar_seconds"),
            },
            sort_keys=True,
        )
        for v in good
    }
    if len(fingerprints) > 1:
        raise ValueError("Batch mixes incompatible backends, units, or protocols")
    complete = bool(rows) and len(good) == len(rows)
    if text_metric:
        counts = {k: sum(r[k] for r in good) for k in ["N", "S", "D", "I", "errors"]}
        value = 100 * counts["errors"] / counts["N"] if counts["N"] else None
        method = "micro_errors_over_reference_units"
    elif metric in ("der", "jer") or metric.startswith("vad_"):
        counts = {}
        for row in good:
            for key, value in row["details"].items():
                counts[key] = counts.get(key, 0) + value
        if metric == "der":
            numerator = sum(
                counts.get(k, 0) for k in ("confusion", "missed detection", "false alarm")
            )
            denominator = counts.get("total", 0)
        elif metric == "jer":
            numerator = counts.get("speaker error", 0)
            denominator = counts.get("speaker count", 0)
        elif metric == "vad_error":
            numerator = counts.get("miss", 0) + counts.get("false alarm", 0)
            denominator = counts.get("total", 0)
        elif metric == "vad_precision":
            numerator = counts.get("relevant retrieved", 0)
            denominator = counts.get("retrieved", 0)
        elif metric == "vad_recall":
            numerator = counts.get("relevant retrieved", 0)
            denominator = counts.get("relevant", 0)
        else:
            numerator = counts.get("true positive", 0) + counts.get("true negative", 0)
            denominator = sum(
                counts.get(k, 0)
                for k in ("true positive", "true negative", "false positive", "false negative")
            )
        value = 100 * numerator / denominator if denominator else None
        method = "micro_pyannote_components"
    else:
        values = [
            r["value"] for r in good if r.get("value") is not None and math.isfinite(r["value"])
        ]
        complete = complete and len(values) == len(rows)
        value = sum(values) / len(values) if values else None
        counts = {}
        method = "utterance_macro"
    return {
        "metric": metric,
        "expected": len(rows),
        "scored": len(good),
        "complete": complete,
        "coverage": len(good) / len(rows) if rows else None,
        "value": value if complete else None,
        "valid_subset_value": value,
        "aggregation": method,
        "counts": counts,
        "rows": rows,
        "settings": shared,
        "backend_protocols": [json.loads(p) for p in sorted(fingerprints)],
    }
