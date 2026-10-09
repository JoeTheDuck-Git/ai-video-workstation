#!/usr/bin/env python3
"""Deterministic technical QC for a local video file.

Requires ffmpeg and ffprobe. Prints one JSON document to stdout.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, check=False)


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fps_value(value: str | None):
    if not value:
        return None
    if "/" in value:
        numerator, denominator = value.split("/", 1)
        den = number(denominator)
        return number(numerator) / den if den else None
    return number(value)


def parse_args():
    parser = argparse.ArgumentParser(description="Inspect a video before final delivery")
    parser.add_argument("video", type=Path)
    parser.add_argument("--profile", choices=("social",), help="Apply a reusable delivery profile")
    parser.add_argument("--require-audio", action="store_true")
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--expected-fps", type=float)
    parser.add_argument("--expected-duration", type=float)
    parser.add_argument("--duration-tolerance", type=float, default=0.12)
    parser.add_argument("--fps-tolerance", type=float, default=0.02)
    parser.add_argument("--target-lufs", type=float, help="Expected integrated loudness in LUFS")
    parser.add_argument("--lufs-tolerance", type=float, default=1.5)
    parser.add_argument("--max-true-peak", type=float, help="Maximum allowed true peak in dBTP")
    parser.add_argument("--sample-times", help="Comma-separated seconds")
    parser.add_argument("--samples", type=int, default=7, help="Even samples when --sample-times is absent")
    parser.add_argument("--samples-dir", type=Path)
    return parser.parse_args()


def finding(severity: str, code: str, message: str, measured=None, expected=None):
    item = {"severity": severity, "code": code, "message": message}
    if measured is not None:
        item["measured"] = measured
    if expected is not None:
        item["expected"] = expected
    return item


def compact_stream(stream: dict):
    keys = (
        "index", "codec_name", "profile", "codec_type", "width", "height", "pix_fmt",
        "color_space", "field_order", "r_frame_rate", "avg_frame_rate", "sample_rate",
        "channels", "channel_layout", "duration", "bit_rate", "nb_frames",
    )
    return {key: stream[key] for key in keys if key in stream}


def close_to(value: float, target: float, tolerance: float = 0.015):
    return abs(value - target) <= tolerance


def social_profile_findings(payload: dict, video: dict | None, audio: list[dict]):
    findings = []
    format_names = set((payload.get("format", {}).get("format_name") or "").split(","))
    if "mp4" not in format_names and "mov" not in format_names:
        findings.append(finding("warning", "social_container", "Social master is preferably MP4", sorted(format_names)))
    if not video:
        return findings

    codec = video.get("codec_name")
    if codec != "h264":
        findings.append(finding("warning", "social_video_codec", "Social compatibility is strongest with H.264", codec, "h264"))
    profile = (video.get("profile") or "").lower()
    if codec == "h264" and "high" not in profile:
        findings.append(finding("warning", "social_h264_profile", "Preferred H.264 profile is High", video.get("profile"), "High"))
    if video.get("field_order") not in (None, "progressive"):
        findings.append(finding("warning", "social_interlaced", "Social video should be progressive", video.get("field_order"), "progressive"))
    if video.get("pix_fmt") != "yuv420p":
        findings.append(finding("warning", "social_pixel_format", "Preferred SDR pixel format is 4:2:0 yuv420p", video.get("pix_fmt"), "yuv420p"))
    if video.get("color_space") not in (None, "bt709"):
        findings.append(finding("warning", "social_color_space", "Preferred SDR color space is BT.709", video.get("color_space"), "bt709"))

    width = number(video.get("width"))
    height = number(video.get("height"))
    if width and height:
        ratio = width / height
        accepted = (9 / 16, 1.0, 4 / 5, 16 / 9)
        if not any(close_to(ratio, candidate) for candidate in accepted):
            findings.append(finding("warning", "social_aspect_ratio", "Uncommon social aspect ratio", ratio, ["9:16", "1:1", "4:5", "16:9"]))
        if min(width, height) < 720:
            findings.append(finding("warning", "social_resolution_low", "Short edge is below 720 pixels", min(width, height), ">=720"))
        elif min(width, height) < 1080:
            findings.append(finding("warning", "social_resolution_below_preferred", "Prefer a 1080-class social master", min(width, height), ">=1080"))

    fps = fps_value(video.get("avg_frame_rate") or video.get("r_frame_rate"))
    common_fps = (23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60)
    if fps is None or not any(close_to(fps, candidate, 0.03) for candidate in common_fps):
        findings.append(finding("warning", "social_frame_rate", "Preserve native frame rate; measured rate is uncommon for social delivery", fps, list(common_fps)))

    if audio:
        primary_audio = audio[0]
        if primary_audio.get("codec_name") != "aac":
            findings.append(finding("warning", "social_audio_codec", "Preferred social audio codec is AAC-LC", primary_audio.get("codec_name"), "aac"))
        if str(primary_audio.get("sample_rate")) != "48000":
            findings.append(finding("warning", "social_sample_rate", "Preferred audio sample rate is 48 kHz", primary_audio.get("sample_rate"), 48000))
        if primary_audio.get("channels") not in (1, 2):
            findings.append(finding("warning", "social_channels", "Social master should normally use mono or stereo audio", primary_audio.get("channels"), [1, 2]))
        bitrate = number(primary_audio.get("bit_rate"))
        if bitrate is not None and bitrate < 128000:
            findings.append(finding("warning", "social_audio_bitrate", "AAC bitrate is below 128 kbps", bitrate, ">=128000"))
    return findings


def main() -> int:
    args = parse_args()
    result = {
        "status": "ok",
        "input": str(args.video.resolve()),
        "profile": args.profile,
        "tools": {},
        "probe": None,
        "observations": {"black": [], "freeze": [], "silence": [], "loudness": None},
        "samples": [],
        "findings": [],
    }

    for tool in ("ffmpeg", "ffprobe"):
        path = shutil.which(tool)
        result["tools"][tool] = path
        if not path:
            result["findings"].append(finding("blocking", f"missing_{tool}", f"{tool} is not installed"))
    if result["findings"]:
        result["status"] = "blocked"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2
    if not args.video.is_file():
        result["status"] = "blocked"
        result["findings"].append(finding("blocking", "input_missing", "Input video does not exist"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    probe_cmd = [
        "ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(args.video)
    ]
    probe = run(probe_cmd)
    if probe.returncode != 0:
        result["status"] = "blocked"
        result["findings"].append(finding("blocking", "probe_failed", probe.stderr.strip() or "ffprobe failed"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    payload = json.loads(probe.stdout)
    streams = payload.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    duration = number(payload.get("format", {}).get("duration"))
    primary_video = video_streams[0] if video_streams else None
    result["probe"] = {
        "duration": duration,
        "size_bytes": int(payload.get("format", {}).get("size", 0) or 0),
        "bit_rate": number(payload.get("format", {}).get("bit_rate")),
        "video_streams": [compact_stream(stream) for stream in video_streams],
        "audio_streams": [compact_stream(stream) for stream in audio_streams],
    }

    if not primary_video:
        result["findings"].append(finding("blocking", "missing_video", "No video stream found"))
    if (args.require_audio or args.profile == "social") and not audio_streams:
        result["findings"].append(finding("blocking", "missing_audio", "Required audio stream not found"))

    if args.profile == "social":
        result["findings"].extend(social_profile_findings(payload, primary_video, audio_streams))
        if args.target_lufs is None:
            args.target_lufs = -16.0
        if args.max_true_peak is None:
            args.max_true_peak = -1.0
        args.lufs_tolerance = 2.0

    if primary_video:
        width = primary_video.get("width")
        height = primary_video.get("height")
        fps = fps_value(primary_video.get("avg_frame_rate") or primary_video.get("r_frame_rate"))
        if args.expected_width is not None and width != args.expected_width:
            result["findings"].append(finding("blocking", "width_mismatch", "Unexpected video width", width, args.expected_width))
        if args.expected_height is not None and height != args.expected_height:
            result["findings"].append(finding("blocking", "height_mismatch", "Unexpected video height", height, args.expected_height))
        if args.expected_fps is not None and (fps is None or abs(fps - args.expected_fps) > args.fps_tolerance):
            result["findings"].append(finding("blocking", "fps_mismatch", "Unexpected frame rate", fps, args.expected_fps))
    if args.expected_duration is not None and (duration is None or abs(duration - args.expected_duration) > args.duration_tolerance):
        result["findings"].append(finding("blocking", "duration_mismatch", "Unexpected duration", duration, args.expected_duration))

    filters_cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(args.video),
        "-vf", "blackdetect=d=0.25:pix_th=0.10,freezedetect=n=-50dB:d=1.5",
    ]
    if audio_streams:
        filters_cmd += ["-af", "silencedetect=n=-50dB:d=1.0"]
    filters_cmd += ["-f", "null", "-"]
    decoded = run(filters_cmd)
    log = decoded.stderr
    if decoded.returncode != 0:
        result["findings"].append(finding("blocking", "decode_failed", "Full decode/filter scan failed", decoded.returncode))
    for start, end in re.findall(r"black_start:([0-9.]+).*?black_end:([0-9.]+)", log):
        result["observations"]["black"].append({"start": float(start), "end": float(end)})
    freeze_starts = [float(v) for v in re.findall(r"freeze_start: ([0-9.]+)", log)]
    freeze_ends = [float(v) for v in re.findall(r"freeze_end: ([0-9.]+)", log)]
    for index, start in enumerate(freeze_starts):
        result["observations"]["freeze"].append({"start": start, "end": freeze_ends[index] if index < len(freeze_ends) else None})
    silence_starts = [float(v) for v in re.findall(r"silence_start: ([0-9.]+)", log)]
    silence_ends = [float(v) for v in re.findall(r"silence_end: ([0-9.]+)", log)]
    for index, start in enumerate(silence_starts):
        result["observations"]["silence"].append({"start": start, "end": silence_ends[index] if index < len(silence_ends) else None})

    if audio_streams:
        loud = run([
            "ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(args.video),
            "-vn", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"
        ])
        blocks = re.findall(r"\{\s*\"input_i\".*?\}", loud.stderr, re.S)
        if blocks:
            try:
                result["observations"]["loudness"] = json.loads(blocks[-1])
            except json.JSONDecodeError:
                pass
        measured_loudness = result["observations"]["loudness"]
        if measured_loudness and args.target_lufs is not None:
            integrated = number(measured_loudness.get("input_i"))
            if integrated is None or abs(integrated - args.target_lufs) > args.lufs_tolerance:
                result["findings"].append(finding(
                    "blocking", "loudness_mismatch", "Integrated loudness is outside the requested tolerance",
                    integrated, {"target_lufs": args.target_lufs, "tolerance": args.lufs_tolerance}
                ))
        if measured_loudness and args.max_true_peak is not None:
            true_peak = number(measured_loudness.get("input_tp"))
            if true_peak is None or true_peak > args.max_true_peak:
                result["findings"].append(finding(
                    "blocking", "true_peak_exceeded", "True peak exceeds the requested maximum",
                    true_peak, args.max_true_peak
                ))

    if args.samples_dir and duration and duration > 0:
        args.samples_dir.mkdir(parents=True, exist_ok=True)
        if args.sample_times:
            times = [float(value.strip()) for value in args.sample_times.split(",") if value.strip()]
        else:
            count = max(1, args.samples)
            times = [(duration * (index + 1)) / (count + 1) for index in range(count)]
        for index, timestamp in enumerate(times):
            if not math.isfinite(timestamp) or timestamp < 0 or timestamp > duration:
                result["findings"].append(finding("warning", "invalid_sample_time", "Sample time is outside the video", timestamp))
                continue
            output = args.samples_dir / f"frame-{index:02d}-{timestamp:.3f}s.jpg"
            sample = run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.6f}",
                "-i", str(args.video), "-frames:v", "1", "-q:v", "2", "-y", str(output)
            ])
            if sample.returncode == 0 and output.is_file() and output.stat().st_size > 0:
                result["samples"].append({"time": timestamp, "path": str(output.resolve())})
            else:
                result["findings"].append(finding("warning", "sample_failed", "Could not extract sample frame", timestamp))

    if result["observations"]["black"]:
        result["findings"].append(finding("warning", "black_intervals", "Black intervals detected; review whether intentional", result["observations"]["black"]))
    if result["observations"]["freeze"]:
        result["findings"].append(finding("warning", "freeze_intervals", "Freeze intervals detected; generated or static shots may be intentional", result["observations"]["freeze"]))
    if result["observations"]["silence"]:
        result["findings"].append(finding("warning", "silence_intervals", "Silence intervals detected; review against the intended mix", result["observations"]["silence"]))

    blocking = any(item["severity"] == "blocking" for item in result["findings"])
    result["status"] = "blocked" if blocking else "pass_with_warnings" if result["findings"] else "pass"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
