"""Private model worker. Upstream algorithms remain responsible for scoring."""

from __future__ import annotations

import hashlib
from importlib.metadata import version, PackageNotFoundError
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import traceback


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact(path):
    p = Path(path).resolve(strict=True)
    if p.is_file():
        return {"path": str(p), "sha256": digest(p)}
    files = {
        str(f.relative_to(p)): digest(f)
        for f in sorted(p.rglob("*"))
        if f.is_file()
        and ".git" not in f.parts
        and "__pycache__" not in f.parts
        and f.suffix
        in (".py", ".json", ".yaml", ".yml", ".bin", ".safetensors", ".onnx", ".pt", ".pth", ".pkl")
    }
    return {
        "path": str(p),
        "sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
        "files": files,
    }


def require(config, key):
    if not config.get(key):
        raise ValueError(f"Missing deployment config: {key}")
    return str(Path(config[key]).resolve(strict=True))


def source_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_audio(path, *, minimum=0.1):
    import numpy as np
    import soundfile as sf

    wave, sr = sf.read(Path(path).resolve(strict=True), dtype="float32")
    if wave.ndim != 1 or not len(wave) or not np.isfinite(wave).all():
        raise ValueError(
            "Model input must be a nonempty finite mono audio file; downmix explicitly"
        )
    if len(wave) / sr < minimum:
        raise ValueError(f"Model profile requires at least {minimum} seconds")
    if not np.any(wave):
        raise ValueError("Silent waveform is outside this speech-quality profile")
    return wave, sr


def score(request):
    import torch
    import numpy as np
    import soxr

    family, config = request["family"], request["config"]
    torch.set_num_threads(config.get("threads", 2))
    hyp, ref = request["hypothesis"], request.get("reference")
    wave, sr = read_audio(hyp, minimum=1.0)
    reference_families = {
        "scoreq_natural_ref",
        "scoreq_synthetic_ref",
        "speaker_similarity",
        "phoneme_similarity",
        "speechbert",
        "speechbert_mhubert",
        "speaker_similarity_wavlm",
        "visqol_speech",
        "visqol_audio",
        "whisper_dwer",
    }
    if family in reference_families:
        if not isinstance(ref, str):
            raise ValueError("This metric requires a reference audio path")
        read_audio(ref, minimum=1.0)
    if family == "whisper_wer" and (not isinstance(ref, str) or not ref.strip()):
        raise ValueError("Whisper WER requires nonempty ground-truth reference text")
    device = config.get("device", "cpu")
    provenance = {"hypothesis": artifact(hyp)}
    backend = {}
    for pkg in ("torch", "torchaudio", "numpy", "soundfile", "soxr"):
        try:
            backend[pkg] = version(pkg)
        except PackageNotFoundError:
            pass
    protocol = {
        "family": family,
        "sample_rate": sr,
        "channel_policy": "strict_mono",
        "minimum_seconds": 1.0,
        "gain_normalization": "none",
        "download_policy": "offline",
        "configuration": {
            k: v for k, v in config.items() if k not in ("python", "timeout", "threads", "device")
        },
    }
    for key in (
        "checkpoint",
        "source_dir",
        "model_dir",
        "config_file",
        "ssl_checkpoint",
        "primary_model",
        "p808_model",
        "source_file",
        "binary",
    ):
        if config.get(key):
            provenance[key] = artifact(require(config, key))
    for key, expected in config.get("expected_hashes", {}).items():
        if key not in provenance or provenance[key]["sha256"] != expected:
            raise ValueError(f"Artifact hash mismatch: {key}")
    if family not in (
        "scoreq_natural_nr",
        "scoreq_natural_ref",
        "scoreq_synthetic_nr",
        "scoreq_synthetic_ref",
        "dnsmos",
        "visqol_speech",
        "visqol_audio",
        "plcmos_v2",
        "plcmos_v2_val",
    ):
        if not config.get("trusted_checkpoint"):
            raise ValueError("Set trusted_checkpoint=true only for trusted local PyTorch artifacts")
    if config.get("source_dir"):
        sys.path.insert(0, require(config, "source_dir"))
    details = {}
    with torch.inference_mode():
        if family == "audiobox_aesthetics":
            from audiobox_aesthetics.infer import initialize_predictor

            model = initialize_predictor(ckpt=require(config, "checkpoint"))
            model.device = device
            model.model.to(device)
            values = model.forward([{"path": hyp}])[0]
            backend["audiobox-aesthetics"] = version("audiobox-aesthetics")
        elif family.startswith("scoreq_"):
            import onnxruntime as ort
            from scoreq import Scoreq

            _, domain, mode = family.split("_")
            options = ort.SessionOptions()
            options.intra_op_num_threads = config.get("threads", 2)
            options.inter_op_num_threads = 1
            providers = (
                ["CPUExecutionProvider"]
                if device == "cpu"
                else ["CUDAExecutionProvider", "CPUExecutionProvider"]
            )
            if device != "cpu" and "CUDAExecutionProvider" not in ort.get_available_providers():
                raise ValueError("Requested CUDA provider is unavailable")
            # Official preprocessing/predict; initialize only the local, explicit session.
            model = Scoreq.__new__(Scoreq)
            model.use_onnx, model.mode, model.data_domain = True, mode, domain
            model.session = ort.InferenceSession(
                require(config, "checkpoint"), sess_options=options, providers=providers
            )
            if mode == "ref":
                if config.get("reference_kind") not in ("matching", "nonmatching"):
                    raise ValueError("Declare reference_kind=matching or nonmatching")
                if domain == "synthetic" and config["reference_kind"] != "nonmatching":
                    raise ValueError(
                        "Synthetic SCOREQ reference profile is nonmatching-reference only"
                    )
                read_audio(ref, minimum=1.0)
                provenance["reference"] = artifact(ref)
            values = {"score": model.predict(hyp, ref_path=ref if mode == "ref" else None)}
            backend.update(scoreq=version("scoreq"), onnxruntime=ort.__version__)
            protocol.update(
                domain=domain,
                mode=mode,
                reference_kind=config.get("reference_kind", "none"),
                scoring_sample_rate=16000,
            )
        elif family == "nisqa":
            from nisqa.NISQA_model import nisqaModel

            args = {
                "mode": "predict_file",
                "pretrained_model": require(config, "checkpoint"),
                "deg": hyp,
                "output_dir": None,
                "num_workers": 0,
                "bs": 1,
                "tr_num_workers": 0,
                "tr_bs_val": 1,
                "tr_parallel": False,
                "device": device,
                "ms_channel": None,
            }
            model = nisqaModel(args)
            frame = model.predict()
            values = {
                k: float(frame.iloc[0][k + "_pred"])
                for k in ("mos", "noi", "dis", "col", "loud")
                if k + "_pred" in frame
            }
            if set(values) != {"mos", "noi", "dis", "col", "loud"}:
                raise ValueError("nisqa family requires the multidimensional nisqa.tar checkpoint")
        elif family == "utmos":
            from speechmos.utmos22.strong.model import UTMOS22Strong

            model = UTMOS22Strong()
            model.load_state_dict(
                torch.load(require(config, "checkpoint"), map_location="cpu", weights_only=False),
                strict=True,
            )
            model.to(device).eval()
            values = {
                "mos": float(model(torch.from_numpy(wave).unsqueeze(0).to(device), sr).item())
            }
            protocol["model"] = "UTMOS22 strong / SpeechMOS conversion"
        elif family == "sheet_ssqa":
            import yaml
            import s3prl.nn
            from unittest.mock import patch

            cfg = yaml.safe_load(Path(require(config, "config_file")).read_text())
            original = s3prl.nn.S3PRLUpstream

            def local_upstream(name, *args, **kwargs):
                kwargs["path_or_url"] = require(config, "ssl_checkpoint")
                kwargs["refresh"] = False
                return original(name, *args, **kwargs)

            from sheet.models.sslmos import SSLMOS

            with patch.object(s3prl.nn, "S3PRLUpstream", side_effect=local_upstream) as patched:
                patched.available_names = original.available_names
                model = SSLMOS(cfg["model_input"], **cfg["model_params"])
            model.load_state_dict(
                torch.load(require(config, "checkpoint"), map_location="cpu", weights_only=False),
                strict=True,
            )
            model.to(device).eval()
            predictor_type = source_module(
                str(Path(config["source_dir"]) / "hubconf.py"), "sheet_local_hub"
            ).Predictor
            predictor = predictor_type(model, cfg)
            tensor = torch.from_numpy(soxr.resample(wave, sr, 16000)).to(device)
            values = {"mos": float(np.asarray(predictor.predict(wav=tensor)).reshape(-1)[0])}
            protocol["inference_mode"] = cfg["inference_mode"]
            protocol.update(resampler="soxr_HQ", scoring_sample_rate=16000)
        elif family == "dnsmos":
            import onnxruntime as ort

            module = source_module(require(config, "source_file"), "dnsmos_official")
            model = module.ComputeScore.__new__(module.ComputeScore)
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = config.get("threads", 2)
            opts.inter_op_num_threads = 1
            if device != "cpu":
                raise ValueError("This DNSMOS profile currently supports CPU only")
            model.onnx_sess = ort.InferenceSession(
                require(config, "primary_model"),
                sess_options=opts,
                providers=["CPUExecutionProvider"],
            )
            model.p808_onnx_sess = ort.InferenceSession(
                require(config, "p808_model"), sess_options=opts, providers=["CPUExecutionProvider"]
            )
            # Official script uses an obsolete positional librosa.resample call.
            # Feed an explicitly resampled temporary WAV; scoring code is unchanged.
            import tempfile
            import soundfile as sf

            with tempfile.TemporaryDirectory() as tmp:
                p = str(Path(tmp) / "audio.wav")
                sf.write(p, soxr.resample(wave, sr, 16000), 16000, subtype="FLOAT")
                raw = model(p, 16000, False)
            values = {
                key: float(raw[key])
                for key in ("SIG", "BAK", "OVRL", "P808_MOS", "SIG_raw", "BAK_raw", "OVRL_raw")
            }
            protocol.update(personalized=False, resampler="soxr_HQ", scoring_sample_rate=16000)
            backend["onnxruntime"] = ort.__version__
        elif family in ("plcmos_v2", "plcmos_v2_val"):
            import onnxruntime as ort

            module = source_module(require(config, "source_file"), "official_plcmos")
            rounds = config.get("embed_rounds", 15)
            seed = config.get("seed", 0)
            if isinstance(rounds, bool) or not isinstance(rounds, int) or not 1 <= rounds <= 1000:
                raise ValueError("embed_rounds must be an integer in [1, 1000]")
            if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
                raise ValueError("seed must be a uint32 integer")
            if device != "cpu":
                raise ValueError("PLCMOS profile uses ONNX CPUExecutionProvider")
            model = module.PLCMOS.__new__(module.PLCMOS)
            model.model_name = family
            model.max_lens = 999999999999
            model.embed_rounds = rounds
            options = ort.SessionOptions()
            options.intra_op_num_threads = config.get("threads", 2)
            options.inter_op_num_threads = 1
            model.session = ort.InferenceSession(
                require(config, "checkpoint"), options, providers=["CPUExecutionProvider"]
            )
            audio16 = soxr.resample(wave, sr, 16000) if sr != 16000 else wave
            if np.max(np.abs(audio16)) > 1:
                raise ValueError("PLCMOS samples must be in [-1,1]; no implicit normalization")
            np.random.seed(seed)
            values = {"mos": model.get_mos(audio16, 16000)}
            protocol.update(
                scoring_sample_rate=16000,
                resampler="soxr_HQ",
                seed=seed,
                embed_rounds=rounds,
                model_version=family,
                random_generator="numpy RandomState (upstream global RNG)",
            )
        else:
            values, details = extended(family, hyp, ref, wave, sr, config, provenance, protocol)
    values = {k: float(v) for k, v in values.items()}
    if not values or not all(math.isfinite(v) for v in values.values()):
        raise ArithmeticError("Upstream returned an empty or nonfinite score")
    protocol["artifact_hashes"] = {
        k: v["sha256"] for k, v in provenance.items() if k not in ("hypothesis", "reference")
    }
    for pkg in (
        "scoreq",
        "onnxruntime",
        "audiobox-aesthetics",
        "transformers",
        "s3prl",
        "espnet",
        "phonemizer",
        "librosa",
        "meeteval",
    ):
        try:
            backend[pkg] = version(pkg)
        except PackageNotFoundError:
            pass
    return {
        "status": "ok",
        "values": values,
        "details": details,
        "backend": backend,
        "protocol": protocol,
        "provenance": provenance,
    }


def extended(family, hyp, ref, wave, sr, config, provenance, protocol):
    import numpy as np
    import torch
    import soxr

    device = config.get("device", "cpu")
    details = {}
    if family != "whisper_wer":
        reference, ref_sr = read_audio(ref, minimum=1.0)
        provenance["reference"] = artifact(ref)
    if family.startswith("visqol_"):
        import re
        import subprocess
        import tempfile
        import soundfile as sf

        if sr != ref_sr or wave.shape != reference.shape:
            raise ValueError(
                "ViSQOL requires equal-length, same-rate aligned inputs; no implicit crop"
            )
        target = 16000 if family == "visqol_speech" else 48000
        if max(np.max(np.abs(wave)), np.max(np.abs(reference))) > 1:
            raise ValueError(
                "ViSQOL PCM input must be within [-1,1]; no implicit gain normalization"
            )
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "ref.wav", Path(tmp) / "hyp.wav"
            sf.write(a, soxr.resample(reference, ref_sr, target), target, subtype="PCM_16")
            sf.write(b, soxr.resample(wave, sr, target), target, subtype="PCM_16")
            command = [
                require(config, "binary"),
                "--reference_file",
                str(a),
                "--degraded_file",
                str(b),
                "--similarity_to_quality_model",
                require(config, "checkpoint"),
            ]
            if family == "visqol_speech":
                command.append("--use_speech_mode")
            output = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=config.get("timeout", 120),
            ).stdout
        match = re.search(r"MOS-LQO:\s*([-+0-9.eE]+)", output)
        if not match:
            raise RuntimeError("ViSQOL did not return MOS-LQO")
        protocol.update(
            scoring_sample_rate=target,
            resampler="soxr_HQ",
            pcm_subtype="PCM_16",
            length_policy="strict_equal",
        )
        return {"mos": float(match.group(1))}, {"stdout": output}
    wave16 = soxr.resample(wave, sr, 16000)
    if family != "whisper_wer":
        reference16 = soxr.resample(reference, ref_sr, 16000)
    protocol.update(scoring_sample_rate=16000, resampler="soxr_HQ")
    if family == "speaker_similarity":
        from espnet2.bin.spk_inference import Speech2Embedding

        model = Speech2Embedding(
            require(config, "config_file"), require(config, "checkpoint"), device=device
        )
        model.spk_model.eval()
        value = torch.cosine_similarity(model(reference16), model(wave16), dim=-1).item()
        return {"cosine": value}, details
    if family in ("speechbert", "speechbert_mhubert"):
        from transformers import HubertModel

        module = source_module(
            str(Path(require(config, "source_dir")) / "discrete_speech_metrics/speechbertscore.py"),
            "official_speechbert",
        )
        model = module.SpeechBERTScore.__new__(module.SpeechBERTScore)
        model.model = (
            HubertModel.from_pretrained(require(config, "model_dir"), local_files_only=True)
            .to(device)
            .eval()
        )
        model.device = device
        model.layer = config.get("layer", 8)
        model.sr = 16000
        p, r, f = model.score(reference16, wave16)
        protocol.update(
            model_type="hubert-base" if family == "speechbert" else "mhubert-147",
            layer=model.layer,
            reference_order="reference first; hypothesis second",
        )
        return {"precision": p, "recall": r, "f1": f}, details
    if family == "speaker_similarity_wavlm":
        from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector

        path = require(config, "model_dir")
        processor = Wav2Vec2FeatureExtractor.from_pretrained(path, local_files_only=True)
        model = WavLMForXVector.from_pretrained(path, local_files_only=True).to(device).eval()

        def embedding(audio):
            inputs = processor(audio, sampling_rate=16000, return_tensors="pt", padding=True)
            return model(**inputs.to(device)).embeddings

        value = torch.cosine_similarity(embedding(reference16), embedding(wave16), dim=-1).item()
        protocol.update(
            model_type="wavlm-base-plus-sv",
            similarity="cosine",
            pooling="upstream x-vector",
            feature_extractor_do_normalize=processor.do_normalize,
        )
        return {"cosine": value}, details
    if family == "phoneme_similarity":
        from .phonemes import compare_decoded
        from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

        path = require(config, "model_dir")
        processor = Wav2Vec2Processor.from_pretrained(path, local_files_only=True)
        model = Wav2Vec2ForCTC.from_pretrained(path, local_files_only=True).to(device).eval()

        def decode(audio):
            values = processor(audio, return_tensors="pt", sampling_rate=16000).input_values.to(
                device
            )
            return processor.batch_decode(model(values).logits.argmax(dim=-1))[0]

        ref_decoded, hyp_decoded = decode(reference16), decode(wave16)
        values, details = compare_decoded(ref_decoded, hyp_decoded)
        protocol["tokenization"] = (
            "Unicode characters of IPA after space removal; legacy PhonemeSimilarity, not phone-token PER"
        )
        protocol["phone_tokenization"] = "space-delimited decoded phonemes; URGENT 2026 LPS"
        return values, details
    if family in ("whisper_wer", "whisper_dwer"):
        from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
        from transformers.models.whisper.english_normalizer import EnglishTextNormalizer
        from .registry import text_metric

        path = require(config, "model_dir")
        processor = AutoProcessor.from_pretrained(path, local_files_only=True)
        model = (
            AutoModelForSpeechSeq2Seq.from_pretrained(
                path, local_files_only=True, torch_dtype=torch.float32
            )
            .to(device)
            .eval()
        )
        if config.get("language", "english") != "english":
            raise ValueError(
                "Whisper WER v2 validated profile uses EnglishTextNormalizer; other languages require a separate profile"
            )
        if len(wave16) > 30 * 16000 or (family == "whisper_dwer" and len(reference16) > 30 * 16000):
            raise ValueError("Whisper v2 profile requires clips <=30s; no silent truncation")
        normalizer = EnglishTextNormalizer({})

        def decode(audio):
            inputs = processor(
                audio, sampling_rate=16000, return_tensors="pt", return_attention_mask=True
            )
            pred = model.generate(
                inputs.input_features.to(device),
                attention_mask=inputs.attention_mask.to(device),
                language="english",
                task="transcribe",
                num_beams=config.get("beam_size", 5),
                do_sample=False,
            )
            return processor.batch_decode(pred, skip_special_tokens=True)[0]

        hyp_text = decode(wave16)
        ref_text = decode(reference16) if family == "whisper_dwer" else ref
        if not isinstance(ref_text, str):
            raise ValueError("whisper_wer reference must be ground-truth transcript text")
        # EnglishTextNormalizer is applied explicitly before the shared MeetEval scorer.
        counts = text_metric(
            metric="wer", reference=normalizer(ref_text), hypothesis=normalizer(hyp_text)
        )
        if counts["value"] is None:
            raise ValueError("Empty normalized ASR reference")
        details = {
            "reference_text": ref_text,
            "hypothesis_text": hyp_text,
            **{k: counts[k] for k in ("N", "S", "D", "I", "errors")},
        }
        protocol.update(
            normalization="Whisper EnglishTextNormalizer({}) then nfkc-casefold-v1",
            beam_size=config.get("beam_size", 5),
            reference_mode="clean_reference_asr"
            if family == "whisper_dwer"
            else "ground_truth_text",
        )
        return {"wer": counts["value"]}, details
    raise ValueError(f"Unsupported model family: {family}")


def main():
    start = time.perf_counter()
    try:
        request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        result = score(request)
    except (ImportError, ModuleNotFoundError) as exc:
        result = {
            "status": "dependency_unavailable",
            "values": {},
            "reason": f"{type(exc).__name__}: {exc}",
        }
    except (ValueError, FileNotFoundError, TypeError) as exc:
        result = {
            "status": "invalid_input",
            "values": {},
            "reason": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
    except Exception as exc:
        result = {
            "status": "backend_error",
            "values": {},
            "reason": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
    result["elapsed_seconds"] = time.perf_counter() - start
    Path(sys.argv[2]).write_text(
        json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
