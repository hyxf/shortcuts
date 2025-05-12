#!/usr/bin/env python3
import os
import subprocess
import argparse
import sys
from typing import List, Optional


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available in the system."""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def generate_output_path(input_path: str, output_ext: str = ".mp4", output_name: Optional[str] = None) -> str:
    """Generate a unique output file path to avoid overwriting."""
    if not output_ext.startswith("."):
        output_ext = f".{output_ext}"
    input_dir = os.path.dirname(input_path) or "."
    base_name = output_name or os.path.splitext(os.path.basename(input_path))[0]

    index = 0
    while True:
        suffix = f"_{index}" if index > 0 else ""
        output_filename = f"{base_name}{suffix}{output_ext}"
        output_path = os.path.join(input_dir, output_filename)
        if not os.path.exists(output_path):
            return output_path
        index += 1


def run_ffmpeg(cmd: List[str]) -> bool:
    """Run ffmpeg command."""
    print(f"[INFO] Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[SUCCESS] Completed: {cmd[-1]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg command failed: {e}", file=sys.stderr)
        return False


def print_file_info(input_path: str, output_path: str) -> None:
    """Print input/output file size information."""
    if os.path.exists(output_path):
        input_size = os.path.getsize(input_path) / 1024 / 1024
        output_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"[INFO] Input size: {input_size:.2f} MB")
        print(f"[INFO] Output size: {output_size:.2f} MB")
        if input_size > 0:
            change_pct = ((output_size / input_size) - 1) * 100
            print(f"[INFO] Size change: {output_size - input_size:.2f} MB ({change_pct:.1f}%)")


def convert_video(args):
    output_path = generate_output_path(args.input, args.ext, args.output)
    cmd = ["ffmpeg", "-y", "-i", args.input, "-c:v", args.vcodec, "-c:a", args.acodec, output_path]
    if run_ffmpeg(cmd):
        print(f"[SUCCESS] Video saved to: {output_path}")
        print_file_info(args.input, output_path)
        return True
    return False


def handle_audio(args):
    """
    Convert audio or extract audio from video based on --extract flag.
    """
    output_path = generate_output_path(args.input, args.ext, args.output)
    
    cmd = ["ffmpeg", "-y", "-i", args.input]

    if args.extract:
        cmd.append("-vn")  # Remove video stream

    cmd.extend(["-c:a", args.acodec])

    if args.bitrate:
        cmd.extend(["-b:a", args.bitrate])
    
    cmd.append(output_path)

    if run_ffmpeg(cmd):
        print(f"[SUCCESS] Audio saved to: {output_path}")
        print_file_info(args.input, output_path)
        return True
    return False


def main():
    if not check_ffmpeg():
        print("[ERROR] ffmpeg is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Media conversion tools using ffmpeg.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Video command
    video_parser = subparsers.add_parser("video", help="Convert video")
    video_parser.add_argument("input", help="Input video file")
    video_parser.add_argument("--ext", default=".mp4", help="Output file extension")
    video_parser.add_argument("--vcodec", default="libx264", help="Video codec")
    video_parser.add_argument("--acodec", default="aac", help="Audio codec")
    video_parser.add_argument("--output", help="Output filename (without extension)")

    # Unified audio command
    audio_parser = subparsers.add_parser("audio", help="Convert or extract audio")
    audio_parser.add_argument("input", help="Input file (audio or video)")
    audio_parser.add_argument("--extract", action="store_true", help="Extract audio from video")
    audio_parser.add_argument("--ext", default=".m4a", help="Output file extension")
    audio_parser.add_argument("--acodec", default="aac", help="Audio codec")
    audio_parser.add_argument("--bitrate", help="Audio bitrate")
    audio_parser.add_argument("--output", help="Output filename (without extension)")

    args = parser.parse_args()

    if not getattr(args, "input", None) or not os.path.exists(args.input):
        print(f"[ERROR] Input file does not exist or not provided: {getattr(args, 'input', '')}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "video":
            success = convert_video(args)
        elif args.command == "audio":
            success = handle_audio(args)
        else:
            parser.print_help()
            sys.exit(0)

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
