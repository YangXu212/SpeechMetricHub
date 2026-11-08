# Windows build notes

The standard-scoring baseline includes a Windows x64 / CPython 3.10 build of upstream MeetEval 0.4.3, without changes to its algorithms. This is not a blanket certification of all model dependencies on Windows.

## Recorded build

- NumPy 1.26.4, SciPy 1.13.1.
- Isolated build: Cython 3.0.12, setuptools 75.8.0.
- MinGW-w64 x86_64, POSIX, SEH, UCRT from the official [niXman/mingw-builds-binaries releases](https://github.com/niXman/mingw-builds-binaries/releases).
- Unmodified PyPI source distribution `meeteval-0.4.3.tar.gz`.

```text
python setup.py build_ext --compiler=mingw32 --define=MS_WIN64 bdist_wheel
```

`MS_WIN64` is required by the 64-bit Windows Python headers in this build. The resulting wheel targets CPython 3.10 / win_amd64. GCC runtime DLLs (`libstdc++-6.dll`, `libgcc_s_seh-1.dll`, `libwinpthread-1.dll`) were loaded from a private directory using `os.add_dll_directory`, without changing system PATH.

The historical deployment used a private dependency directory rather than modifying Torch/NumPy/SciPy in the inference environment. `run.py` retains optional `_vendor` support for that deployment pattern; normal pip installations do not need it. No private vendor directory or compiler binary is included in this public repository.

Rebuild and test when changing Python ABI or compiler. An existing cp310 wheel cannot be assumed to work on another ABI. Preserve upstream dependency licenses with any redistributed binaries. On a fresh Windows machine, provision a supported compiler/toolchain and verify the installed package before relying on it.
