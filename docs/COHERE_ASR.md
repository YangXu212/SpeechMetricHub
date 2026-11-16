# Cohere Transcribe recognition metrics

The Cohere backend uses the locally provisioned
[`CohereLabs/cohere-transcribe-03-2026`](https://huggingface.co/CohereLabs/cohere-transcribe-03-2026)
checkpoint through the native Hugging Face Transformers implementation. It supplies
an alternative recognizer for speech evaluation; it does not replace Whisper or
change existing metric IDs. All four scores are percentages; lower is better.

| Metric | Reference | Scoring units |
|---|---|---|
| `cohere_wer` | Ground-truth transcript | Normalized whitespace-delimited words |
| `cohere_cer` | Ground-truth transcript | Normalized Unicode letters, marks and numbers |
| `cohere_dwer` | Clean reference audio, transcribed by the same model | Words |
| `cohere_dcer` | Clean reference audio, transcribed by the same model | Characters |

WER and CER from one `evaluate` call share transcription. The two ground-truth
heads belong to `cohere_wer`; the two audio-reference heads belong to
`cohere_dwer`. Scores produced by different recognizers are different evaluation
protocols, even when both are named WER.

## Scientific meaning and limits

With `N` reference units, `S` substitutions, `D` deletions and `I` insertions,
the error rate is `100 * (S + D + I) / N`. Recognition counts use SpeechMetricHub's
existing MeetEval backend. Corpus aggregation sums the counts before division;
it does not average utterance WER percentages. Empty normalized references have
an undefined rate and retain insertions for corpus accounting. An incomplete
batch must not be presented as the complete dataset's score.

The transcript-reference metrics measure agreement with supplied text. Only use
text covering the audio actually scored: a complete sentence is not a valid
ground truth for a truncated recording. The audio-reference metrics measure
agreement between two automatic transcriptions. The reference transcript is a
pseudo-reference and can itself be wrong. Identical ASR errors on both sides can
produce a low dWER/dCER despite incorrect speech; these are not substitutes for
ground-truth WER/CER or listening tests.

Normalization is the existing `nfkc-casefold-v1` protocol: Unicode NFKC,
case folding, punctuation as word boundaries, apostrophes retained inside words,
no number verbalization, and fillers retained. CER removes whitespace and
punctuation. This is **not a claim of reproducing Cohere's leaderboard scoring
normalizer or reported benchmark numbers**. Prefer CER/dCER for Chinese and
Japanese rather than treating a sentence without spaces as one word. The model
card itself reports CER for Chinese, Japanese and Korean.

The official model card warns that Cohere Transcribe may hallucinate on silence
or non-speech noise, has no automatic language detection, and provides neither
timestamps nor speaker diarization. SpeechMetricHub therefore keeps the selected
language explicit and does not silently insert VAD, remove quiet sections, or
replace silent-input predictions with empty text. A VAD-gated experiment would
need a separately recorded preprocessing protocol. No detector establishes that
this ASR model is hallucination-free.

## Audio and decoding protocol

- Input files must be finite, mono audio and at least 0.1 seconds long. Stereo
  requires an explicit upstream channel selection; there is no hidden downmix.
- Waveforms are read as float32 and resampled to 16 kHz with soxr HQ when needed.
  There is no gain fitting, amplitude normalization or silence trimming added
  by SpeechMetricHub.
- Local `AutoProcessor` and `CohereAsrForConditionalGeneration` are loaded with
  `local_files_only=True` and `trust_remote_code=False`. Inference uses
  safetensors. No cloud transcription API is called and audio is not uploaded.
- The default language is `en`, punctuation is enabled, beam size is 1,
  sampling is disabled, and `max_new_tokens=256` applies per output chunk.
  Chunk generation is processed in batches of one by default to bound GPU
  memory; `chunk_batch_size` is recorded and can be configured explicitly.
  The language codes supported upstream are `ar de el en es fr it ja ko nl pl
  pt vi zh`; language selection is an experiment parameter, not auto-detection.
- CPU defaults to float32 and CUDA to bfloat16. Device, precision, generation
  arguments, dependency versions and model artifact identity are part of the
  reported protocol. A precision change is not assumed numerically equivalent.
- The native processor owns long-audio splitting and reconstruction. In
  Transformers 5.4.0, the default maximum chunk is 35 seconds with a 5-second
  quiet-boundary search window. This window is **not overlapping audio**.
  `audio_chunk_index` and language are passed to the native decoder so all chunk
  texts are reassembled in order. Actual loaded processor settings are recorded.
- The native feature extractor includes deterministic dither keyed to each
  chunk's valid waveform length. It is retained, rather than independently
  disabled or replaced. Attention masks and decoder prompts are preserved.
- If a generated chunk lacks EOS before its token budget is exhausted, return
  `generation_truncated` with no valid score. Do not score a silently incomplete
  transcription. Forced EOS at the token limit is disabled so it cannot conceal
  truncation. Input duration also has an explicit resource limit, default
  600 seconds, rather than an implicit crop.

Transformers 5.4.0's long-form reassembler can raise an indexing error when all
decoded chunks are empty. The adapter handles only this verified empty-output
case by retaining the empty transcription and records the guard in decode
diagnostics; it does not discard nonempty hallucinated text.

The standard interface does not add timestamps, speaker assignment or
speaker-permutation search. In target-speaker experiments, select the correct
target reference upstream; never choose whichever reference produces the lowest
error.

## Environment and deployment

The official model card recommends native **Transformers >= 5.4.0**, and states
that testing used **PyTorch 2.10.0** while other versions are expected to work.
That expectation is not a validation result for PyTorch 2.8. Keep the Cohere
worker environment separate from the existing Transformers 4.48.2 environment
used by other SpeechMetricHub model families. Consult the release validation
record for the exact versions and hardware actually exercised.

Native inference needs Transformers, PyTorch, Hugging Face Hub, soundfile,
librosa, sentencepiece, protobuf and the matching tokenizer implementation.
Accelerate is required when using automatic device placement; SpeechMetricHub
uses an explicit selected device. Scoring additionally needs MeetEval and
kaldialign. Do not upgrade the main environment in place simply to satisfy the
new model's Transformers dependency.

Provision the model through the official access process or an authorized,
verified local copy. The checkpoint license is Apache-2.0; Hugging Face access
may require accepting the repository's access conditions. Keep weights outside
the wheel and Git repository. Deployment configuration records the local model
directory and its artifact hashes. Do not publish another user's local files or
credentials with a configuration example.

After provisioning the family configurations in a deployment lock:

The [Cohere overlay](../requirements-cohere.txt) belongs in a separate venv with
access to the primary profile's packages. The primary environment retains its
own Transformers version. The v0.8 validation exercises Torch 2.8.0+cu128 with
Transformers 5.4.0; the official card's Torch 2.10 recommendation is not used as
a substitute for these actual tests. A fully independent environment is also
possible if all required dependencies are installed there.

```bash
# Use your provisioned base environment's Python.
python -m venv --system-site-packages /opt/speechmetrichub-cohere
/opt/speechmetrichub-cohere/bin/python -m pip install -r requirements-cohere.txt
/opt/speechmetrichub-cohere/bin/python -m pip install --no-deps .
/opt/speechmetrichub-cohere/bin/python -m pip check
```

Match the base runtime's pip/setuptools constraints if the new venv shadows
them with incompatible versions. The tested worker's full inventory, including
inherited packages and overlay precedence, is checked by the deployment lock.

Create the worker lock **inside that worker environment**, using the
[example family settings](../examples/cohere_deployment.json). In a parent
deployment, add the same family settings plus `python` (worker interpreter) and
`worker_deployment` (worker lock file). Parent locking verifies the child lock
inside its interpreter and checks the effective configurations agree. It also
hashes the child lock; changing either environment requires intentional
revalidation and new locks. No nested worker routing is supported.

GPU profiles use an explicit `cuda:N` and `dtype="bfloat16"` or `"float32"`.
The shared home installation uses CPU/float32 for node-independent calls;
select an available card in a separately created GPU deployment before running
large batches. Per-call model loading is retained; this release does not add a
persistent model server.

```python
from speechmetrichub import MetricHub

hub = MetricHub("/path/to/deployment.locked.json")
gt = hub.evaluate(
    ["cohere_wer", "cohere_cer"],
    reference="The correct transcript for this recording.",
    hypothesis="generated.wav",
)
paired = hub.evaluate(
    ["cohere_dwer", "cohere_dcer"],
    reference="clean.wav",
    hypothesis="generated.wav",
)
```

Inspect `status`, the generated reference/hypothesis text, `N/S/D/I`, and decode
diagnostics before comparing scores. Do not interpret a successful import as a
successful model invocation.

## Reproducing validation

Release v0.8 was exercised with PyTorch 2.8.0+cu128 and Transformers 5.4.0:
24 native/API head comparisons cover three real pairs, silence, white noise and
a 40.17-second two-chunk recording on g12 / RTX 4090 / bfloat16. Four invalid
inputs and an intentionally insufficient token budget are checked separately.
A CPU/float32 paired-audio invocation was also exercised. These are integration
fixtures rather than a corpus accuracy benchmark or cross-precision equality
claim. In the white-noise fixture, both native and wrapped inference produced
"Thank you."; the words are retained as insertions against an empty reference.

`scripts/validate_cohere.py` compares the public metric interfaces with a direct
native Transformers processor/model/generate/decode invocation under matched
weights, device, precision and decoding parameters. It retains generated text,
input hashes, count comparisons, dependency versions and timing. The direct
model is released before the metric workers start, avoiding duplicate GPU model
allocations during this check.

The manifest is explicit and must contain paired audio plus valid ground-truth
text for the transcript-reference checks. Validation also exercises long-audio
chunk reconstruction, a deliberately insufficient token budget, silence/noise,
empty reference text and malformed inputs. Silence/noise transcripts are
observations, not asserted empty outputs. Timing includes documented startup
costs and is not a full-dataset throughput claim.

## Sources

- [Official model card and access/license information](https://huggingface.co/CohereLabs/cohere-transcribe-03-2026)
- [Cohere's Transcribe documentation](https://docs.cohere.com/docs/transcribe)
- [Native Transformers Cohere ASR documentation](https://huggingface.co/docs/transformers/model_doc/cohere_asr)
- [Transformers 5.4.0 processor](https://github.com/huggingface/transformers/blob/v5.4.0/src/transformers/models/cohere_asr/processing_cohere_asr.py)
- [Transformers 5.4.0 feature extractor](https://github.com/huggingface/transformers/blob/v5.4.0/src/transformers/models/cohere_asr/feature_extraction_cohere_asr.py)
- [MeetEval](https://github.com/fgnt/meeteval)

中文提示：Cohere 的 WER/CER 与 Whisper 是不同识别器协议，不应混用历史
分数。dWER/dCER 的参考来自自动识别，并非人工真值。静音或噪声仍可能触发
幻觉；接口会保留真实输出，不自动改成空文本或“满分”。
