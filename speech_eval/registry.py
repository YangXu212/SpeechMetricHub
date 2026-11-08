"""Discoverable registry. No model download or import at discovery time."""

from importlib import import_module
from importlib.metadata import PackageNotFoundError
import json
from pathlib import Path

_CUSTOM = {}


def list_metrics(domain=None, *, category=None, reference_kind=None):
    entries = json.loads(Path(__file__).with_name("metrics.json").read_text(encoding="utf-8"))
    entries += [entry for entry, _ in _CUSTOM.values()]
    return [
        entry
        for entry in entries
        if (domain is None or domain in entry["domains"])
        and (category is None or entry.get("category") == category)
        and (reference_kind is None or reference_kind in entry.get("reference_kinds", []))
    ]


def get_metric(name):
    spec = next((m for m in list_metrics() if m["id"] == name), None)
    if spec is None:
        raise ValueError(f"Unknown metric: {name}; use list_metrics()")
    return spec


def register(
    name,
    function,
    *,
    domains,
    description,
    source,
    category="custom",
    reference_kinds=(),
    direction="descriptive",
    unit="unspecified",
):
    if not callable(function):
        raise TypeError("Metric adapter must be callable")
    if any(m["id"] == name for m in list_metrics()):
        raise ValueError(f"Duplicate metric: {name}")
    if direction not in ("higher_is_better", "lower_is_better", "descriptive"):
        raise ValueError("Invalid score direction")
    _CUSTOM[name] = (
        {
            "id": name,
            "domains": list(domains),
            "description": description,
            "source": source,
            "category": category,
            "reference_kinds": list(reference_kinds),
            "direction": direction,
            "unit": unit,
            "implementation": "custom",
            "status": "user_registered",
        },
        function,
    )


def run(name, **inputs):
    if name in _CUSTOM:
        return _CUSTOM[name][1](**inputs)
    spec = get_metric(name)
    module, function = spec["adapter"].split(":")
    try:
        return getattr(import_module(module), function)(metric=name, **inputs)
    except (ImportError, PackageNotFoundError) as exc:
        return {
            "metric": name,
            "status": "dependency_unavailable",
            "value": None,
            "reason": str(exc),
            "required": spec.get("dependencies", []),
        }


def text_metric(*, metric, reference, hypothesis, collar=5):
    from .transcription import score, protocol

    # SISO / TS-ASR callers supply the target transcript, never a best-of-speakers selection.
    unit = "char" if metric.endswith("cer") else "word"
    perm = metric.startswith(("cp", "tcp"))

    def segments(value):
        return [{"speaker": "target", "text": value}] if isinstance(value, str) else value

    ref, hyp = segments(reference), segments(hypothesis)
    if metric.startswith("ts_"):
        for rows in [ref, hyp]:
            if (
                len({str(s.get("speaker", "target")) for s in rows if s.get("text", "").strip()})
                > 1
            ):
                raise ValueError(
                    "TS-ASR requires the specified target stream only; no best-speaker selection"
                )
    result = score(
        ref, hyp, unit=unit, permutation=perm, collar=collar if metric.startswith("tcp") else None
    )
    return {
        **result,
        "metric": metric,
        "value": result["rate"],
        "value_unit": "percent",
        "status": "ok" if result["N"] else "undefined_reference",
        "protocol": protocol(),
    }


def cardinality_metric(*, metric, reference, hypothesis, **kwargs):
    from .cardinality import evaluate_speaker_count

    result = evaluate_speaker_count(reference, hypothesis, **kwargs)
    return {
        **result,
        "metric": metric,
        "count_status": result["status"],
        "status": "ok" if result["available"] else "unavailable",
        "value": result["absolute_error"],
        "value_unit": "speakers",
        "aggregation": "utterance_macro_MAE; report exact-count accuracy separately",
    }
