"""Independent upstream comparisons for v0.4; requires explicit public sources.

Upstream directory: speechbertscore.py, urgent_intrusive.py, mcd_utils.py,
urgent_lps.py. See docs/EXPANSION_PROFILES.md for their official sources.
"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import soundfile as sf
import torch


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def main():
    p = argparse.ArgumentParser()
    for key in ("config", "fixtures", "upstream", "results", "output"):
        p.add_argument("--" + key, required=True)
    args = p.parse_args()
    torch.set_num_threads(2)
    c = json.loads(Path(args.config).read_text())
    results = json.loads(Path(args.results).read_text())
    up = Path(args.upstream)
    sys.path.insert(0, str(up))
    ref, sr = sf.read(Path(args.fixtures) / "ref.wav", dtype="float32")
    hyp, _ = sf.read(Path(args.fixtures) / "noisy.wav", dtype="float32")
    rows = {}

    def check(name, actual, expected, tolerance=1e-5):
        delta = abs(float(actual) - float(expected))
        rows[name] = dict(
            adapter=float(actual),
            upstream=float(expected),
            absolute_error=delta,
            tolerance=tolerance,
            passed=delta <= tolerance,
        )
        Path(args.output).write_text(json.dumps(rows, indent=2) + "\n")
        print(name, rows[name], flush=True)

    with torch.inference_mode():
        from transformers import HubertModel, Wav2Vec2FeatureExtractor, WavLMForXVector

        for family, prefix, group in [
            ("speechbert", "speechbert_", "speechbert_precision"),
            ("speechbert_mhubert", "speechbert_mhubert_", "speechbert_mhubert_precision"),
        ]:
            encoder = HubertModel.from_pretrained(
                c[family]["model_dir"], local_files_only=True
            ).eval()
            # Independent direct feature extraction/matrix reductions, without the toolkit adapter.
            a = encoder(torch.from_numpy(ref)[None], output_hidden_states=True).hidden_states[8][0]
            b = encoder(torch.from_numpy(hyp)[None], output_hidden_states=True).hidden_states[8][0]
            sim = (
                torch.nn.functional.normalize(b, dim=-1)
                @ torch.nn.functional.normalize(a, dim=-1).T
            )
            precision = float(sim.max(dim=1).values.mean())
            recall = float(sim.max(dim=0).values.mean())
            for head, val in [
                ("precision", precision),
                ("recall", recall),
                ("f1", 2 * precision * recall / (precision + recall)),
            ]:
                check(
                    prefix + head,
                    results["model_cases"][group]["degraded"][prefix + head]["value"],
                    val,
                )
            del encoder, a, b, sim
        path = c["speaker_similarity_wavlm"]["model_dir"]
        processor = Wav2Vec2FeatureExtractor.from_pretrained(path, local_files_only=True)
        encoder = WavLMForXVector.from_pretrained(path, local_files_only=True).eval()
        a = encoder(
            **processor(ref, sampling_rate=sr, padding=True, return_tensors="pt")
        ).embeddings
        b = encoder(
            **processor(hyp, sampling_rate=sr, padding=True, return_tensors="pt")
        ).embeddings
        expected = torch.nn.functional.cosine_similarity(a, b, dim=-1).item()
        check(
            "speaker_similarity_wavlm",
            results["model_cases"]["speaker_similarity_wavlm"]["degraded"][
                "speaker_similarity_wavlm"
            ]["value"],
            expected,
        )
        del encoder
        # Current official URGENT class; redirect only the model identifier to a local cache.
        from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

        official = module(up / "urgent_lps.py", "urgent_lps_reference")
        local_path = c["phoneme_similarity"]["model_dir"]
        proc_loader = Wav2Vec2Processor.from_pretrained
        model_loader = Wav2Vec2ForCTC.from_pretrained
        with (
            patch.object(
                Wav2Vec2Processor,
                "from_pretrained",
                side_effect=lambda *a, **k: proc_loader(local_path, local_files_only=True),
            ),
            patch.object(
                Wav2Vec2ForCTC,
                "from_pretrained",
                side_effect=lambda *a, **k: model_loader(local_path, local_files_only=True),
            ),
        ):
            scorer = official.LevenshteinPhonemeSimilarity(device="cpu")
        scorer.phoneme_predictor.model.eval()
        check(
            "lps_phone",
            results["model_cases"]["phoneme_similarity"]["degraded"]["lps_phone"]["value"],
            scorer(ref, hyp),
        )
        del scorer
    for family in ("plcmos_v2", "plcmos_v2_val"):
        official = module(c[family]["source_file"], "official_" + family)
        import onnxruntime as ort

        factory = ort.InferenceSession
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        with patch.object(
            official.ort,
            "InferenceSession",
            side_effect=lambda *a, **kw: factory(
                c[family]["checkpoint"], options, providers=["CPUExecutionProvider"]
            ),
        ):
            scorer = official.PLCMOS(embed_rounds=15)
        np.random.seed(0)
        expected = scorer.get_mos(hyp, sr)
        check(family, results["model_cases"][family]["degraded"][family]["value"], expected, 1e-7)
    official = module(up / "urgent_intrusive.py", "urgent_intrusive_reference")
    a = ref.astype("float64")
    b = hyp.astype("float64")
    for name, fn in [("lsd_urgent", official.lsd_metric), ("mcd_urgent", official.mcd_metric)]:
        check(name, results["spectral_cases"][name]["degraded"]["value"], fn(a, b, sr), 1e-7)
    # Independent analytic dB LSD gain fixture: halving amplitude is 20*log10(2) dB.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from speechmetrichub import run

    analytic_ref = np.random.default_rng(31).normal(0, 0.1, 16000)
    analytic = run(
        "lsd_db", reference=analytic_ref, hypothesis=analytic_ref * 0.5, sample_rate=16000
    )
    check("lsd_db", analytic["value"], 20 * np.log10(2), 1e-7)
    # c1 MCD uses the public extractor, then independently computes its declared DTW convention.
    mcd = module(up / "mcd_utils.py", "mcd_reference")
    from fastdtw import fastdtw
    from scipy.spatial.distance import euclidean

    a = mcd.sptk_extract(a, sr, n_fft=1024, n_shift=256, mcep_dim=None, mcep_alpha=None)[:, 1:]
    b = mcd.sptk_extract(b, sr, n_fft=1024, n_shift=256, mcep_dim=None, mcep_alpha=None)[:, 1:]
    _, path = fastdtw(a, b, radius=1, dist=euclidean)
    expected = np.mean([10 / np.log(10) * np.sqrt(2) * euclidean(a[i], b[j]) for i, j in path])
    check(
        "mcd_dtw_c1", results["spectral_cases"]["mcd_dtw_c1"]["degraded"]["value"], expected, 1e-7
    )
    if not all(row["passed"] for row in rows.values()):
        raise SystemExit("Parity failed")


if __name__ == "__main__":
    main()
