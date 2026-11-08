# Troubleshooting

| Symptom | Check / resolution |
|---|---|
| `dependency_unavailable` | Install the appropriate extra in the interpreter that actually runs the scorer. Run `python -m pip check`. |
| MeetEval/PESQ compilation fails | Install a compatible compiler toolchain; use Python 3.10/3.11. See Windows notes. |
| No checkpoint or source code found | Fill the local configuration; model extras do not bundle weights or every upstream repository. |
| SCOREQ/ONNX dependency conflict | Use a dedicated environment; the tested SCOREQ profile expects ONNX Runtime 1.16.3. Do not mix CPU/GPU distributions. |
| `Artifact hash mismatch` | Verify whether weights/source changed. Restore the recorded artifact or deliberately create a new profile; do not silently delete the hash constraint. |
| `invalid_input` for stereo, short or silent audio | The model profile requires finite mono audio, >=1 second, with nonzero signal. Prepare/downmix explicitly and record the transformation. |
| SI-SDR/BSS returns `nonfinite_result` | Perfect or degenerate cases can be infinite. Inspect the waveform; do not replace with zero. |
| Quality prediction seems implausible | Confirm model training domain, mode, output head and direction. Runtime correctness is not domain validity. |
| DER rejects transcript spans | Supply genuine activity annotations and UEM. A sentence's first-to-last word span is not necessarily continuous speech activity. |
| Batch score is null | Inspect coverage and per-item failure reasons; a subset score is separate. |
| Batch rejects mixed protocols | Compare normalization, collar, units, model/source hashes and input preprocessing. Score incompatible conditions separately. |
| First model call is slow | Every recording starts a new worker and loads artifacts. Group heads with `evaluate`; persistent model serving is not implemented. |
| `doctor` looks healthy but inference fails | Doctor is inspection, not inference. Run the real validation harness with your configuration. |

When reporting an issue, include a minimal public/synthetic reproduction, the exact metric ID, versions, protocol and relevant hashes. Remove credentials, private audio and personal paths.
