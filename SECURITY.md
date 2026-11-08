# Security and trust boundaries

SpeechMetricHub is a local research library, not a multi-tenant scoring service.

- Deployment configurations are trusted inputs. They select interpreters, source code, executables and model artifacts. Do not accept an arbitrary configuration from an untrusted remote caller.
- PyTorch checkpoint loading may deserialize Python objects. Enable `trusted_checkpoint` only for verified artifacts; use `expected_hashes` to enforce the intended contents.
- Worker processes provide dependency and resource isolation, not a security sandbox.
- Model scoring is configured for local artifacts. Inspect upstream code and licenses before use. An environment inspection is not a runtime security audit.
- Do not put credentials, private recordings or absolute machine-specific deployment files in a public issue.

For a suspected vulnerability, contact the maintainer through their GitHub profile with a minimal description before disclosing sensitive details in a public issue. No private advisory channel or response-time guarantee is currently advertised.
