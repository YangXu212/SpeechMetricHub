"""Additional reference implementations with explicit protocol parameters."""

from importlib.metadata import version
import math


def multistream(*, metric, reference, hypothesis, collar=5.0):
    import dataclasses
    import meeteval.wer as wer
    from .transcription import _segments, NORMALIZATION

    names = {
        "orcwer": "orc_word_error_rate",
        "tcorcwer": "time_constrained_orc_wer",
        "mimower": "mimo_word_error_rate",
        "tcmimower": "time_constrained_mimo_word_error_rate",
        "greedy_dicpwer": "greedy_di_cp_word_error_rate",
        "greedy_ditcpwer": "greedy_di_tcp_word_error_rate",
    }
    timed = metric in ("tcorcwer", "tcmimower", "greedy_ditcpwer")
    if (
        not isinstance(collar, (int, float))
        or isinstance(collar, bool)
        or not math.isfinite(collar)
        or collar < 0
    ):
        raise ValueError("collar must be finite and nonnegative")
    kwargs = (
        dict(
            collar=collar,
            reference_pseudo_word_level_timing="character_based",
            hypothesis_pseudo_word_level_timing="character_based_points",
            reference_sort="segment",
            hypothesis_sort="segment",
        )
        if timed
        else {}
    )
    result = getattr(wer, names[metric])(
        _segments(reference, "word", timed), _segments(hypothesis, "word", timed), **kwargs
    )
    detail = dataclasses.asdict(result)
    return {
        "metric": metric,
        "status": "ok" if result.length else "undefined_reference",
        "value": 100 * result.errors / result.length if result.length else None,
        "value_unit": "percent",
        "N": result.length,
        "S": result.substitutions,
        "D": result.deletions,
        "I": result.insertions,
        "errors": result.errors,
        "details": detail,
        "backend": {"meeteval": version("meeteval")},
        "protocol": {
            "normalization": NORMALIZATION,
            "algorithm": names[metric],
            "assignment_scope": "recording",
            **kwargs,
        },
    }


def bss(*, metric, reference, hypothesis, filter_length=512, permutation=True, zero_mean=False):
    import numpy as np
    import fast_bss_eval

    ref, hyp = np.asarray(reference, dtype=np.float64), np.asarray(hypothesis, dtype=np.float64)
    if ref.ndim != 2 or hyp.shape != ref.shape or not ref.shape[0] or not ref.shape[1]:
        raise ValueError("BSS inputs require equal [sources, samples] arrays")
    if (
        not np.isfinite(ref).all()
        or not np.isfinite(hyp).all()
        or np.any(np.sum(ref**2, axis=-1) == 0)
        or np.any(np.sum(hyp**2, axis=-1) == 0)
    ):
        raise ValueError("BSS requires finite, nonsilent sources")
    if (
        isinstance(filter_length, bool)
        or not isinstance(filter_length, int)
        or not 1 <= filter_length <= ref.shape[1]
    ):
        raise ValueError("filter_length must be a positive integer <= signal length")
    output = fast_bss_eval.bss_eval_sources(
        ref, hyp, filter_length=filter_length, compute_permutation=permutation, zero_mean=zero_mean
    )
    sdr, sir, sar = output[:3]
    perm = output[3] if permutation else np.arange(ref.shape[0])
    values = {"bss_sdr": sdr, "bss_sir": sir, "bss_sar": sar}[metric]
    finite = np.isfinite(values).all()
    return {
        "metric": metric,
        "status": "ok" if finite else "nonfinite_result",
        "value": float(np.mean(values)) if finite else None,
        "per_source": [float(x) if np.isfinite(x) else None for x in values],
        "permutation": perm.tolist(),
        "value_unit": "dB",
        "backend": {"fast_bss_eval": version("fast-bss-eval")},
        "protocol": {
            "filter_length": filter_length,
            "permutation": permutation,
            "zero_mean": zero_mean,
            "source_aggregation": "macro",
            "length_policy": "strict_equal",
        },
    }


def correlations(*, metric, reference, hypothesis):
    import numpy as np
    from scipy import stats

    ref, hyp = np.asarray(reference, dtype=float), np.asarray(hypothesis, dtype=float)
    if (
        ref.ndim != 1
        or ref.shape != hyp.shape
        or len(ref) < 3
        or not np.isfinite(ref).all()
        or not np.isfinite(hyp).all()
    ):
        raise ValueError("Correlation requires >=3 paired finite ratings")
    if np.ptp(ref) == 0 or np.ptp(hyp) == 0:
        return {"metric": metric, "status": "undefined_constant", "value": None}
    result = {"plcc": stats.pearsonr, "srcc": stats.spearmanr, "ktau": stats.kendalltau}[metric](
        ref, hyp
    )
    return {
        "metric": metric,
        "status": "ok",
        "value": float(result.statistic),
        "pvalue": float(result.pvalue),
        "pairs": len(ref),
        "backend": {"scipy": version("scipy")},
        "protocol": {"mapping": "none", "unit": "paired_ratings", "aggregation": "dataset_level"},
    }
