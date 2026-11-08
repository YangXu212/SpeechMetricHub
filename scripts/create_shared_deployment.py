"""Create a locked CLI/API entry point in an explicitly provisioned shared directory.

Run with the installed evaluation environment's Python, after real inference
validation. This does not install packages, download models, or edit shell startup.
"""

import argparse
import json
from pathlib import Path
import shlex
import sys

from speechmetrichub import create_deployment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    manifest = create_deployment(json.loads(Path(args.config).read_text()))
    lock = root / "deployment.locked.json"
    lock.write_text(json.dumps(manifest, indent=2) + "\n")
    executable = Path(sys.executable).absolute()
    entry = root / "bin" / "smh"
    entry.parent.mkdir(exist_ok=True)
    entry.write_text(
        "#!/usr/bin/env bash\n"
        + f"export SPEECHMETRICHUB_DEPLOYMENT={shlex.quote(str(lock))}\n"
        + f'exec {shlex.quote(str(executable))} -m speechmetrichub "$@"\n'
    )
    entry.chmod(0o755)
    activation = root / "activate.sh"
    activation.write_text(
        "# Source explicitly in a shell where you want the evaluation Python.\n"
        + f"export SPEECHMETRICHUB_DEPLOYMENT={shlex.quote(str(lock))}\n"
        + f"export SPEECHMETRICHUB_PYTHON={shlex.quote(str(executable))}\n"
        + f'export PATH={shlex.quote(str(entry.parent) + ":" + str(executable.parent))}:"$PATH"\n'
    )
    print(json.dumps({"lock": str(lock), "command": str(entry), "activate": str(activation)}))


if __name__ == "__main__":
    main()
