"""Portable legacy CLI; optional local _vendor support is separate from pip installs."""
import os
from pathlib import Path
import sys

base=Path(__file__).resolve().parent
vendor=base/'_vendor'
if vendor.is_dir():
    sys.path.insert(0,str(vendor))
    if os.name=='nt' and (vendor/'.libs').is_dir():
        _dll_handle=os.add_dll_directory(str(vendor/'.libs'))

from speech_eval.cli import main
if __name__=='__main__':
    raise SystemExit(main())
