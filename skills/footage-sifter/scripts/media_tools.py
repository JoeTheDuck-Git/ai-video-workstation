"""Locate ffmpeg binaries without writing into an installed Python package."""
import os
import shutil
import warnings
from pathlib import Path


def find_ffmpeg_pair(allow_fetch=True):
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if ffmpeg and ffprobe:
        return ffmpeg, ffprobe
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import static_ffmpeg
        package = Path(static_ffmpeg.__file__).resolve().parent
        for binary in package.glob("bin/*/ffmpeg"):
            probe = binary.with_name("ffprobe")
            if binary.is_file() and probe.is_file() and os.access(binary, os.X_OK):
                return str(binary), str(probe)
        if allow_fetch:
            from static_ffmpeg import run
            return run.get_or_fetch_platform_executables_else_raise()
    except (ImportError, OSError, PermissionError):
        pass
    return None, None


if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffmpeg", action="store_true")
    parser.add_argument("--ffprobe", action="store_true")
    args = parser.parse_args()
    ffmpeg, ffprobe = find_ffmpeg_pair()
    value = ffprobe if args.ffprobe else ffmpeg
    if not value:
        sys.exit("找不到 ffmpeg/ffprobe；請先安裝 ffmpeg")
    print(value)
