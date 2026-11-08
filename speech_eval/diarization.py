"""Explicit speech-activity reference and scoring region required for DER/JER."""

from importlib.metadata import version


def diarization_metric(
    *,
    metric,
    reference,
    hypothesis,
    uem,
    reference_is_speech_activity=False,
    collar=0.0,
    skip_overlap=False,
):
    if not reference_is_speech_activity:
        raise ValueError(
            "Sentence spans are not verified speech-activity annotations; confirm reference quality explicitly"
        )
    if not uem:
        raise ValueError("Explicit UEM scoring intervals required")
    import math

    if not math.isfinite(collar) or collar < 0:
        raise ValueError("Invalid collar")
    from pyannote.core import Annotation, Segment, Timeline
    from pyannote.metrics.diarization import DiarizationErrorRate, JaccardErrorRate
    from pyannote.metrics.detection import (
        DetectionErrorRate,
        DetectionPrecision,
        DetectionRecall,
        DetectionAccuracy,
    )

    def annotation(rows):
        result = Annotation()
        for i, s in enumerate(rows):
            a, b = s["start"], s["end"]
            if (
                not math.isfinite(a)
                or not math.isfinite(b)
                or not 0 <= a < b
                or not s.get("speaker")
            ):
                raise ValueError("Invalid diarization segment")
            result[Segment(a, b), i] = str(s["speaker"])
        return result

    for a, b in uem:
        if not math.isfinite(a) or not math.isfinite(b) or not 0 <= a < b:
            raise ValueError("Invalid UEM")
    classes = {
        "der": DiarizationErrorRate,
        "jer": JaccardErrorRate,
        "vad_error": DetectionErrorRate,
        "vad_precision": DetectionPrecision,
        "vad_recall": DetectionRecall,
        "vad_accuracy": DetectionAccuracy,
    }
    scorer = classes[metric](collar=collar, skip_overlap=skip_overlap)
    detail = scorer(
        annotation(reference),
        annotation(hypothesis),
        uem=Timeline([Segment(a, b) for a, b in uem]),
        detailed=True,
    )
    value = float(abs(scorer)) * 100
    return {
        "metric": metric,
        "status": "ok" if math.isfinite(value) else "nonfinite_result",
        "value": value if math.isfinite(value) else None,
        "details": {k: float(v) for k, v in detail.items()},
        "unit": "percent",
        "backend": {"pyannote.metrics": version("pyannote.metrics")},
        "protocol": {"collar": collar, "skip_overlap": skip_overlap, "uem": uem},
    }
