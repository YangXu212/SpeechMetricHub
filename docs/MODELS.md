# Model setup and artifacts

Start from [deployment.example.json](../examples/deployment.example.json). Its paths are placeholders. Configurations map **family names** to trusted local files; `evaluate` selects the requested output heads. Keep your actual deployment configuration outside version control.

## Common settings

| Field | Meaning |
|---|---|
| `device` | `cpu` by default, or explicit `cuda:N` |
| `threads` | Integer 1–64; default 2 |
| `timeout` | Worker time limit in seconds; default 600 (1200 recommended for ASR) |
| `python` | Optional interpreter for a dedicated worker environment |
| `worker_deployment` | Required lock path whenever `python` points to an alternate interpreter |
| `trusted_checkpoint` | Explicitly permit trusted PyTorch checkpoint deserialization |
| `expected_hashes` | Map artifact field names to SHA-256; mismatch rejects the call |

Workers enforce offline Hugging Face behavior and use only supplied local artifacts. Source repositories can execute Python code; only configure trusted sources. Separate processes are not a security sandbox. Discovery and `doctor` never load models.

## Model families and required artifacts

### Quality, aesthetics, echo and content models

| Family | Outputs | Required local artifacts / source |
|---|---|---|
| `audiobox_aesthetics` | CE, CU, PC, PQ | Official [Audiobox Aesthetics](https://github.com/facebookresearch/audiobox-aesthetics) `checkpoint.pt` |
| `scoreq_natural_nr` | MOS | [SCOREQ](https://github.com/alessandroragano/scoreq) `adapt_nr_telephone.onnx` |
| `scoreq_natural_ref` | Distance | `fixed_nmr_telephone.onnx`, explicit `reference_kind` |
| `scoreq_synthetic_nr` | MOS | `adapt_nr_synthetic.onnx` |
| `scoreq_synthetic_ref` | Distance | `fixed_nmr_synthetic.onnx`, `reference_kind="nonmatching"` |
| `dnsmos` | SIG/BAK/OVRL, raw heads, P808_MOS | [DNSMOS](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) script, `sig_bak_ovr.onnx`, `model_v8.onnx` |
| `nisqa` | MOS, NOI, DIS, COL, LOUD | [NISQA](https://github.com/gabrielmittag/NISQA) source and `nisqa.tar` |
| `utmos` | MOS | [SpeechMOS](https://github.com/tarepan/SpeechMOS) source and `utmos22_strong_step7459_v1.pt` |
| `sheet_ssqa` | MOS | [SHEET](https://github.com/unilight/sheet) source, config, scoring checkpoint, SSL checkpoint |
| `plcmos_v2` | MOS | Microsoft SpeechMOS 0.0.1.1 `plcmos.py`, final v2 ONNX |
| `plcmos_v2_val` | MOS | Same public scorer, separately provisioned v2 validation ONNX |
| `aecmos_16k`, `aecmos_16k_scenarioless`, `aecmos_48k` | ECHO, DEG | Microsoft AECMOS `aecmos.py` and matching ONNX checkpoint; see [AEC_VERIFICATION.md](AEC_VERIFICATION.md) |
| `visqol_speech` | MOS-LQO | [ViSQOL](https://github.com/google/visqol) binary and 16 kHz speech lattice TFLite model |
| `visqol_audio` | MOS-LQO | ViSQOL binary and 48 kHz `libsvm_nu_svr_model.txt` |
| `speechbert` | Precision, recall, F1 | [DiscreteSpeechMetrics](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) source, [HuBERT base](https://huggingface.co/facebook/hubert-base-ls960), layer 8 |
| `speechbert_mhubert` | Precision, recall, F1 | DiscreteSpeechMetrics source, [mHuBERT-147](https://huggingface.co/utter-project/mHuBERT-147), layer 8 |
| `phoneme_similarity` | IPA character similarity, phone-token LPS | Local [wav2vec2-lv-60-espeak-cv-ft](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft) directory |

### Speaker identity models

| Family | Outputs | Required local artifacts / source |
|---|---|---|
| `speaker_similarity` | Cosine | [ESPnet RawNet3](https://huggingface.co/espnet/voxcelebs12_rawnet3) `config.yaml` and `40epoch.pth` |
| `speaker_similarity_wavlm` | Cosine | [WavLM-base-plus-SV](https://huggingface.co/microsoft/wavlm-base-plus-sv) model directory |
| `speaker_similarity_unispeech_wavlm` | Cosine | Local `WavLM-Large.pt` (`ssl_checkpoint`) and [Microsoft UniSpeech](https://github.com/microsoft/UniSpeech/tree/main/downstreams/speaker_verification) `wavlm_large_finetune.pth` (`checkpoint`), `s3prl` installed |

### Speech recognition (ASR) models

| Family | Outputs | Required local artifacts / source |
|---|---|---|
| `whisper_wer_en_openai`, `whisper_dwer_en_openai` | WER and N/S/D/I | Local OpenAI Whisper `large-v3.pt` (`checkpoint`), `openai-whisper==20250625`, `espnet`, `Levenshtein`; **recommended** for paper reproduction — see [WHISPER_ASR.md](WHISPER_ASR.md) |
| `whisper_wer_hf_v3`, `whisper_dwer_hf_v3` | WER and N/S/D/I | Local Hugging Face [whisper-large-v3](https://huggingface.co/openai/whisper-large-v3) directory (`model_dir`); upgraded long-form & fallback decoding — see [WHISPER_ASR.md](WHISPER_ASR.md) |
| `whisper_wer`, `whisper_dwer` | WER and N/S/D/I | Local Hugging Face whisper-large-v3 directory (`model_dir`); legacy v0.2 compatibility profile (`<=30s`) |
| `cohere_wer`, `cohere_dwer` | WER, CER and N/S/D/I | Local [CohereLabs/cohere-transcribe-03-2026](https://huggingface.co/CohereLabs/cohere-transcribe-03-2026) directory and isolated Transformers 5.4 worker — see [COHERE_ASR.md](COHERE_ASR.md) |
| `cohere_wer_en_whisper`, `cohere_dwer_en_whisper`, `cohere_cer_zh_basic`, `cohere_dcer_zh_basic` | WER or CER and N/S/D/I | Same local Cohere snapshot and worker with explicit Whisper/basic cleaners — see [COHERE_PROFILES.md](COHERE_PROFILES.md) |

## Source revisions and adaptations

[validation/environment.json](../validation/environment.json) and the per-release validation reports record exact upstream source commits and artifact hashes. Implementation adaptations are limited to initialization and I/O:

- SCOREQ retains official preprocessing/predict with an explicitly configured ONNX session.
- SHEET injects a local SSL checkpoint and passes an explicitly resampled tensor to the original Predictor.
- SpeechBERTScore loads local HuBERT/mHuBERT weights and retains upstream feature matching/pooling.
- DNSMOS receives a 16 kHz float WAV, avoiding an obsolete positional resampling call in the historical script.
- UniSpeech WavLM-Large-ECAPA injects a local `WavLM-Large.pt` path into S3PRL `UpstreamExpert` rather than downloading at runtime.
- OpenAI Whisper supports CUDA `float16` weight loading while retaining `float32` `LayerNorm` parameters to halve VRAM footprint without altering `fp16=True` matrix multiplications.

## Inspect, lock, then execute

```bash
speechmetrichub doctor --config deployment.local.json --verify-hashes
speechmetrichub lock-deployment --input deployment.local.json --output deployment.locked.json
speechmetrichub verify-deployment --input deployment.locked.json
```

See [DEPLOYMENT_LOCKS.md](DEPLOYMENT_LOCKS.md) and [SHARED_DEPLOYMENT.md](SHARED_DEPLOYMENT.md) for multi-environment lock verification and shared cluster setup.
