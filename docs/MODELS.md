# Model setup and artifacts

Start from [deployment.example.json](../examples/deployment.example.json). Its paths are placeholders. Configurations map **family names** to trusted local files; `evaluate` selects the requested output heads. Keep your actual deployment configuration outside version control.

## Common settings

| Field | Meaning |
|---|---|
| `device` | `cpu` by default, or explicit `cuda:N`; recorded model validation is CPU only |
| `threads` | Integer 1–64; default 2 |
| `timeout` | Worker time limit in seconds; default 600 |
| `python` | Optional interpreter for a separate model environment |
| `trusted_checkpoint` | Explicitly permit trusted PyTorch checkpoint deserialization |
| `expected_hashes` | Map artifact field names to SHA-256; mismatch rejects the call |

The worker sets offline Hugging Face behavior and uses supplied local artifacts. Source repositories can execute Python code; only configure trusted sources. Separate processes are not a security sandbox. Discovery/doctor do not load models. `doctor` checks the current interpreter, not every configured alternate interpreter.

## Families and complete outputs

| Family | Outputs | Required artifacts / source |
|---|---|---|
| `audiobox_aesthetics` | CE, CU, PC, PQ | Official [Audiobox Aesthetics](https://github.com/facebookresearch/audiobox-aesthetics) `checkpoint.pt` |
| `scoreq_natural_nr` | MOS | [SCOREQ](https://github.com/alessandroragano/scoreq) `adapt_nr_telephone.onnx` |
| `scoreq_natural_ref` | Distance | `fixed_nmr_telephone.onnx`, explicit `reference_kind` |
| `scoreq_synthetic_nr` | MOS | `adapt_nr_synthetic.onnx` |
| `scoreq_synthetic_ref` | Distance | `fixed_nmr_synthetic.onnx`, `reference_kind="nonmatching"` |
| `dnsmos` | SIG/BAK/OVRL, their raw heads, P808_MOS | [DNSMOS](https://github.com/microsoft/DNS-Challenge/tree/master/DNSMOS) script, `sig_bak_ovr.onnx`, `model_v8.onnx` |
| `nisqa` | MOS, NOI, DIS, COL, LOUD | [NISQA](https://github.com/gabrielmittag/NISQA) source and multidimensional `nisqa.tar` |
| `utmos` | MOS | [SpeechMOS](https://github.com/tarepan/SpeechMOS) source, `utmos22_strong_step7459_v1.pt` |
| `sheet_ssqa` | MOS for the selected SSL-MOS config | [SHEET](https://github.com/unilight/sheet) source, config, scoring checkpoint, SSL checkpoint |
| `speechbert` | Precision, recall, F1 | [DiscreteSpeechMetrics](https://github.com/Takaaki-Saeki/DiscreteSpeechMetrics) source, [HuBERT base](https://huggingface.co/facebook/hubert-base-ls960), layer 8 |
| `speaker_similarity` | Cosine | [ESPnet RawNet3](https://huggingface.co/espnet/voxcelebs12_rawnet3) config and `40epoch.pth` |
| `phoneme_similarity` | IPA character similarity and phone-token LPS | Local [wav2vec2 phoneme model](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft) directory |
| `visqol_speech` | MOS-LQO | [ViSQOL](https://github.com/google/visqol) binary and speech lattice TFLite model |
| `visqol_audio` | MOS-LQO | ViSQOL binary and `libsvm_nu_svr_model.txt` |
| `whisper_wer`, `whisper_dwer` | WER and N/S/D/I | Local [Whisper large-v3](https://huggingface.co/openai/whisper-large-v3), English, beam 5 |

The SCOREQ ONNX weights are linked by the original project in [Zenodo record 15739280](https://zenodo.org/records/15739280). Acquire weights from the upstream project, check their licenses, and compare their hashes to the recorded profile. Do not substitute a same-shaped model merely because inference succeeds.

## Source revisions and identities

[validation/environment.json](../validation/environment.json) records the exact official source commits used for SHEET, NISQA, SpeechMOS and DiscreteSpeechMetrics, plus artifact hashes for every family. These are the reproducibility baseline, not a promise that a future `main` branch behaves identically.

For example, clone an upstream source and check out the commit recorded in that file. Set `source_dir` to the checkout; keep weights separately. Model-specific `expected_hashes` come from the corresponding artifact field names. Directory fingerprints include relevant code/config/weight files, so changing source files changes the profile.

Implementation adaptations are limited to initialization and I/O:

- SCOREQ retains official preprocessing/predict with an explicitly configured ONNX session.
- SHEET injects a local SSL checkpoint and passes an explicitly resampled tensor to the original Predictor.
- SpeechBERTScore loads local HuBERT weights and retains upstream feature matching/pooling.
- DNSMOS receives a 16 kHz float WAV, avoiding an obsolete positional resampling call in the historical script.

## Inspect, then execute

```bash
speechmetrichub doctor --config deployment.local.json --verify-hashes
python scripts/validate_models.py \
  --config deployment.local.json \
  --hypothesis /audio/noisy.wav \
  --reference /audio/clean.wav \
  --nonmatching-reference /audio/other-clean.wav \
  --reference-text "the actual ground truth transcript" \
  --output validation.local.json
```

Use `--families audiobox_aesthetics scoreq_natural_nr` to run a subset. A configuration file is not a runtime result: retain the actual report from your machine. GPU paths, all other model variants, languages and distortion domains are not implied to be validated by the recorded CPU baseline.

## v0.4 additions

| Family | Complete outputs | Artifacts |
|---|---|---|
| `speechbert_mhubert` | precision, recall, F1 | Public DiscreteSpeechMetrics source; local utter-project/mHuBERT-147; layer 8 |
| `speaker_similarity_wavlm` | cosine | microsoft/wavlm-base-plus-sv model directory including feature extractor config |
| `plcmos_v2` | MOS | Microsoft SpeechMOS 0.0.1.1 `plcmos.py`; final v2 ONNX |
| `plcmos_v2_val` | MOS | Same public scorer; separately provisioned v2 validation ONNX |

See [complete profile definitions](EXPANSION_PROFILES.md), [example configuration](../examples/deployment.example.json) and [recorded v0.4 identities](../validation/expansion-v0.4.json). The existing `phoneme_similarity` family now computes both character and phone-token outputs in one inference. Choose the explicit `lps_phone` metric ID for the latter.

## v0.5 AEC / verification and deployment locks

See [AECMOS, ERLE, EER and minDCF profiles](AEC_VERIFICATION.md) and [locked worker deployment](DEPLOYMENT_LOCKS.md).
