"""Native MeetEval scoring. Local code only normalizes and adapts I/O/UI data.

One call is one recording: never reset speaker assignment within a recording.
For CER, normalized Unicode characters become separate MeetEval tokens.
"""

from importlib.metadata import version
import hashlib
import json
import math
import re
import unicodedata

VERSION = "speech-eval-mt-v1.0"
NORMALIZATION = {
    "id": "nfkc-casefold-v1",
    "unicode": "NFKC",
    "case": "casefold",
    "punctuation": "word boundaries; preserve apostrophe inside a word",
    "characters": "Unicode letters, marks and numbers; no whitespace or punctuation",
    "initialisms": "T_V_ style letter sequences become TV",
    "numbers": "no verbalization",
    "fillers": "retained",
    "chinese": "CER; no implicit Chinese word segmentation",
}
TIME_PROTOCOL = {
    "collars_seconds": [2, 5],
    "reference_timing": "character_based",
    "hypothesis_timing": "character_based_points",
    "ordering": "segment",
    "timestamp_tolerance_seconds": 0.05,
    "approximate": True,
}


def normalize(text):
    text = unicodedata.normalize("NFKC", str(text or ""))
    for char in ["\u2019", "\u2018", "\u02bc"]:
        text = text.replace(char, "'")
    text = re.sub(r"\b(?:[A-Za-z]_){2,}", lambda m: m.group().replace("_", ""), text).casefold()
    chars = []
    for i, char in enumerate(text):
        if unicodedata.category(char)[0] in "LNM":
            chars.append(char)
        elif (
            char == "'"
            and 0 < i < len(text) - 1
            and text[i - 1].isalnum()
            and text[i + 1].isalnum()
        ):
            chars.append(char)
        else:
            chars.append(" ")
    return " ".join("".join(chars).split())


def tokenize(text, unit):
    text = normalize(text)
    if unit == "word":
        return text.split()
    if unit != "char":
        raise ValueError("unit must be word or char")
    return [c for c in text if unicodedata.category(c)[0] in "LNM"]


def language(text):
    return "zh" if re.search("[\u3400-\u9fff\U00020000-\U0002fa1f]", text) else "en"


def _start(segment):
    try:
        value = float(segment.get("start", 0))
        return value if math.isfinite(value) else 0.0
    except (TypeError, ValueError):
        return 0.0


def valid_time(segment, duration=None):
    values = [segment.get("start"), segment.get("end")]
    if any(
        isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x)
        for x in values
    ):
        return False
    start, end = values
    return start >= 0 and end > start and (duration is None or end <= duration + 0.05)


def backend_info():
    # Do not silently substitute a handwritten implementation when deps are absent.
    return {
        "engine": "MeetEval",
        "meeteval": version("meeteval"),
        "kaldialign": version("kaldialign"),
        "numpy": version("numpy"),
        "scipy": version("scipy"),
    }


def protocol():
    return {
        "id": VERSION,
        "backend": backend_info(),
        "normalization": NORMALIZATION,
        "time": TIME_PROTOCOL,
        "assignment_scope": "one recording per call",
        "aggregation": "sum errors / sum reference units; split by corpus and unit",
        "empty_reference": "rate=null; insertions retained in corpus numerator",
        "failure_policy": "report every item; incomplete coverage has no complete-set score",
        "official_moss_parity": False,
        "official_chime_parity": False,
        "sources": [
            "https://github.com/fgnt/meeteval",
            "https://github.com/fgnt/meeteval/blob/main/doc/tcpwer.md",
        ],
    }


def _segments(segments, unit, timed):
    from meeteval.io import SegLST

    rows = []
    for index, s in sorted(enumerate(segments), key=lambda p: (_start(p[1]), p[0])):
        tokens = tokenize(s.get("text", ""), unit)
        if not tokens:
            continue
        row = {
            "words": " ".join(tokens),
            "speaker": str(s.get("speaker") or "未标注"),
            "original_index": index,
        }
        if timed:
            if not valid_time(s):
                raise ValueError("invalid timestamp")
            row.update(start_time=float(s["start"]), end_time=float(s["end"]))
        rows.append(row)
    return SegLST(rows)


def _word_rows(rows):
    return [{**s, "words": word} for s in rows for word in s["words"].split()]


def _alignment(ref, hyp, collar):
    if collar is not None:
        from meeteval.wer.wer.time_constrained import align

        return align(
            ref,
            hyp,
            collar=collar,
            style="seglst",
            reference_pseudo_word_level_timing="character_based",
            hypothesis_pseudo_word_level_timing="character_based_points",
            reference_sort="segment",
            hypothesis_sort="segment",
        )
    import kaldialign

    rr, hh = _word_rows(ref), _word_rows(hyp)
    # NUL cannot occur in normalized tokens.
    aligned = kaldialign.align([s["words"] for s in rr], [s["words"] for s in hh], "\x00")
    result = []
    i = j = 0
    for a, b in aligned:
        r = rr[i] if a != "\x00" else None
        h = hh[j] if b != "\x00" else None
        i += a != "\x00"
        j += b != "\x00"
        result.append((r, h))
    return result


def score(ref_segments, hyp_segments, unit="word", permutation=True, collar=None):
    from meeteval.io import SegLST
    from meeteval.wer.wer.cp import cp_word_error_rate
    from meeteval.wer.wer.siso import siso_word_error_rate
    from meeteval.wer.wer.time_constrained import tcp_word_error_rate

    if collar is not None and (not permutation or not math.isfinite(collar) or collar < 0):
        raise ValueError("tcp requires permutation and finite nonnegative collar")
    ref = _segments(ref_segments, unit, collar is not None)
    hyp = _segments(hyp_segments, unit, collar is not None)
    rg, hg = ref.groupby("speaker"), hyp.groupby("speaker")
    if collar is not None:
        er = tcp_word_error_rate(
            ref,
            hyp,
            collar=collar,
            reference_pseudo_word_level_timing="character_based",
            hypothesis_pseudo_word_level_timing="character_based_points",
            reference_sort="segment",
            hypothesis_sort="segment",
        )
    elif permutation:
        er = cp_word_error_rate(ref, hyp, reference_sort=False, hypothesis_sort=False)
    else:
        er = siso_word_error_rate(
            " ".join(s["words"] for s in ref), " ".join(s["words"] for s in hyp)
        )
    pairs = er.assignment if permutation else [(None, None)]
    ops = []
    assignments = []
    for pair_index, (r, h) in enumerate(pairs):
        rr = rg.get(r, SegLST([])) if permutation else ref
        hh = hg.get(h, SegLST([])) if permutation else hyp
        aligned = _alignment(rr, hh, collar)
        pair_ops = []
        ref_words, hyp_words = _word_rows(rr), _word_rows(hh)
        ri = hi = 0
        for a, b in aligned:
            op = (
                "I" if a is None else "D" if b is None else "C" if a["words"] == b["words"] else "S"
            )
            context = ref_words if ref_words else hyp_words
            pos = ri if ref_words else hi
            pair_ops.append(
                {
                    "op": op,
                    "ref": a["words"] if a else "",
                    "hyp": b["words"] if b else "",
                    "ref_segment": a["original_index"] if a else None,
                    "hyp_segment": b["original_index"] if b else None,
                    "ref_speaker": a["speaker"] if a else None,
                    "hyp_speaker": b["speaker"] if b else None,
                    "pair": pair_index,
                    "context_tokens": [s["words"] for s in context[max(0, pos - 3) : pos + 4]]
                    if op != "C"
                    else [],
                    "context_source": "ref" if ref_words else "hyp",
                    **(
                        {
                            "ref_time": [float(a["start_time"]), float(a["end_time"])]
                            if a
                            else None,
                            "hyp_time": [float(b["start_time"]), float(b["end_time"])]
                            if b
                            else None,
                        }
                        if collar is not None
                        else {}
                    ),
                }
            )
            ri += a is not None
            hi += b is not None
        ct = {key: sum(o["op"] == key for o in pair_ops) for key in ["S", "D", "I"]}
        assignments.append(
            {
                "reference": r,
                "hypothesis": h,
                "N": len(ref_words),
                "H": len(hyp_words),
                **ct,
                "errors": sum(ct.values()),
            }
        )
        ops.extend(pair_ops)
    counts = {"S": int(er.substitutions), "D": int(er.deletions), "I": int(er.insertions)}
    observed = {k: sum(o["op"] == k for o in ops) for k in counts}
    if observed != counts:
        raise RuntimeError(f"Upstream score/alignment mismatch: {observed} != {counts}")
    return {
        "unit": unit,
        "permutation": permutation,
        "time_constrained": collar is not None,
        "collar_seconds": collar,
        "rate": 100 * er.errors / er.length if er.length else None,
        "errors": int(er.errors),
        "N": int(er.length),
        "H": len(_word_rows(hyp)),
        **counts,
        "ops": ops,
        "assignment": assignments if permutation else [],
        "reference_speakers": len(rg),
        "hypothesis_speakers": len(hg),
        "unmatched_reference": int(er.missed_speaker) if permutation else None,
        "unmatched_hypothesis": int(er.falarm_speaker) if permutation else None,
        "backend": backend_info(),
    }


def generation_health(raw, segments):
    """Check preservation of spoken text without guessing why generation stopped."""
    if raw is None:
        return {"status": "not_checked", "complete": None, "reasons": []}
    text = re.sub(r"\[[^\]]*\]|<[^>]*>", "", raw)
    raw_chars = "".join(tokenize(text, "char"))
    parsed_chars = "".join(tokenize(" ".join(s.get("text", "") for s in segments), "char"))
    complete = raw_chars == parsed_chars
    return {
        "status": "ok" if complete else "unparsed_text",
        "complete": complete,
        "raw_text_units": len(raw_chars),
        "parsed_text_units": len(parsed_chars),
        "reasons": []
        if complete
        else ["原始生成文本与已解析分段不一致；分数仅覆盖已解析内容，完整结果暂不可评分。"],
    }


def evaluate(
    ref_segments, hyp_segments, *, has_reference=True, duration=None, boundary_note="", raw=None
):
    ref_segments = ref_segments or []
    hyp_segments = hyp_segments or []
    lang = language(" ".join(str(s.get("text", "")) for s in ref_segments or hyp_segments))
    config = protocol()
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "protocol": config,
                "ref": ref_segments,
                "hyp": hyp_segments,
                "reference": has_reference,
                "duration": duration,
                "boundary": boundary_note,
                "raw": raw,
            },
            ensure_ascii=False,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    health = generation_health(raw, hyp_segments)
    result = {
        "version": VERSION,
        "fingerprint": fingerprint,
        "language": lang,
        "normalization": NORMALIZATION,
        "backend": config["backend"],
        "protocol": config,
        "generation": health,
        "available": has_reference,
        "primary": "cp_cer" if lang == "zh" else "cp_wer",
        "metrics": {},
        "warnings": list(health["reasons"]),
        "tie_break": "Upstream MeetEval / kaldialign alignment; optimal assignment may not be unique",
        "scope": "one clip, one global assignment; standard library, local normalization; not a full benchmark",
        "timing": {
            "available": False,
            "protocol": TIME_PROTOCOL,
            "quality": "unavailable",
            "reasons": [],
        },
        "diarization": {
            "available": False,
            "reason": "句段参考未经语音活动审核，暂不用于 DER；统一库另提供需显式确认参考质量的 DER 接口。",
        },
        "sources": config["sources"],
        "reference_complete": not bool(boundary_note),
    }
    if not has_reference:
        result["warnings"].append("没有参考标注，不能计算错误率。")
        return result
    if boundary_note:
        result["warnings"].append("参考未完整覆盖边界残句；保留诊断评分，不计入完整协议成绩。")
    reasons = []
    labels_ok = True
    for side, segs in [("参考", ref_segments), ("模型", hyp_segments)]:
        invalid = [
            i
            for i, s in enumerate(segs)
            if tokenize(s.get("text", ""), "char") and not valid_time(s, duration)
        ]
        if invalid:
            reasons.append(
                f"{side}第 {', '.join(str(i + 1) for i in invalid)} 段时间戳缺失、零长度或越界；不计算 tcp。"
            )
        if any(
            not str(s.get("speaker") or "").strip()
            for s in segs
            if tokenize(s.get("text", ""), "char")
        ):
            labels_ok = False
            reasons.append(f"{side}有缺失说话人标签；文本诊断中合为未标注流，不计入完整协议成绩。")
    result["warnings"].extend(reasons)
    result["timing"].update(
        available=not reasons,
        quality="unavailable" if reasons else "segment_approximation",
        reasons=reasons,
        boundary_incomplete=bool(boundary_note),
        note="句段插值估计词/字位置；不是逐词时间精度。",
    )
    eligible = health["complete"] is not False and not boundary_note and labels_ok
    for unit in ["char"] if lang == "zh" else ["word", "char"]:
        suffix = "cer" if unit == "char" else "wer"
        specs = [(True, None, "cp_"), (False, None, "concat_")]
        if not reasons:
            specs += [(True, c, "tcp_") for c in TIME_PROTOCOL["collars_seconds"]]
        for perm, collar, prefix in specs:
            metric = score(ref_segments, hyp_segments, unit, perm, collar)
            metric["label"] = (
                ("tcp" if collar is not None else "cp" if perm else "拼接 ")
                + suffix.upper()
                + (f" · {collar}s" if collar is not None else "")
            )
            metric["eligible"] = eligible
            metric["status"] = "ok" if eligible else "diagnostic_only"
            result["metrics"][prefix + suffix + (f"_{collar}s" if collar is not None else "")] = (
                metric
            )
    if not reasons:
        result["primary"] = "tcp_cer_5s" if lang == "zh" else "tcp_wer_5s"
    if not result["metrics"][result["primary"]]["N"]:
        result["warnings"].append("参考归一化后为空，单条率为未定义；插入数仍计入语料总数。")
    return result
