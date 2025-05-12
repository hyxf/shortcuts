#!/usr/bin/env python3
import datetime
import os
import subprocess
import argparse
import sys
from typing import List, Optional

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".flac", ".wav"}


def check_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def list_media_files(directory: str, media_type: str = "all") -> List[str]:
    if media_type == "video":
        exts = VIDEO_EXTENSIONS
    elif media_type == "audio":
        exts = AUDIO_EXTENSIONS
    else:
        exts = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS

    return [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, f)) and os.path.splitext(f)[1].lower() in exts
    ]


def generate_output_path(input_path: str, output_ext: str = ".mp4", output_name: Optional[str] = None) -> str:
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
    print(f"[INFO] Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[SUCCESS] -> {cmd[-1]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg failed: {e}", file=sys.stderr)
        return False


def print_file_info(input_path: str, output_path: str) -> None:
    if os.path.exists(output_path):
        input_size = os.path.getsize(input_path) / 1024 / 1024
        output_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"[INFO] Size: {input_size:.2f} MB → {output_size:.2f} MB ({output_size - input_size:+.2f} MB)")


def convert_video(input_file: str, args) -> None:
    output_path = generate_output_path(input_file, args.ext)
    cmd = ["ffmpeg", "-y", "-i", input_file, "-c:v", args.vcodec, "-c:a", args.acodec, output_path]
    if run_ffmpeg(cmd):
        print_file_info(input_file, output_path)


def convert_audio(input_file: str, args) -> None:
    output_path = generate_output_path(input_file, args.ext)
    cmd = ["ffmpeg", "-y", "-i", input_file]
    if args.extract:
        cmd.append("-vn")
    cmd.extend(["-c:a", args.acodec])
    if args.bitrate:
        cmd.extend(["-b:a", args.bitrate])
    cmd.append(output_path)
    if run_ffmpeg(cmd):
        print_file_info(input_file, output_path)


def download_m3u8(url: str, args) -> None:
    output_dir = args.dir

    if args.output:
        base_name = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"output_{timestamp}"

    output_path = generate_output_path(os.path.join(output_dir, base_name), ".mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-allowed_extensions",
        "ALL",
        "-i",
        url,
        "-c:v",
        args.vcodec,
        "-c:a",
        args.acodec,
        output_path,
    ]
    run_ffmpeg(cmd)


def process_inputs(inputs: List[str], handler, args) -> None:
    for item in inputs:
        print(f"\n[PROCESSING] {item}")
        try:
            handler(item, args)
        except Exception as e:
            print(f"[ERROR] Failed to process {item}: {e}", file=sys.stderr)


def main():
    if not check_ffmpeg():
        print("[ERROR] ffmpeg is not available.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Media converter using ffmpeg (single or batch)")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    video_parser = subparsers.add_parser("video", help="Convert video file(s)")
    video_parser.add_argument("input", help="Input file or directory")
    video_parser.add_argument("--ext", default=".mp4", help="Output extension")
    video_parser.add_argument("--vcodec", default="libx264", help="Video codec")
    video_parser.add_argument("--acodec", default="aac", help="Audio codec")

    audio_parser = subparsers.add_parser("audio", help="Convert or extract audio file(s)")
    audio_parser.add_argument("input", help="Input file or directory")
    audio_parser.add_argument("--extract", action="store_true", help="Extract audio from video")
    audio_parser.add_argument("--ext", default=".m4a", help="Output extension")
    audio_parser.add_argument("--acodec", default="aac", help="Audio codec")
    audio_parser.add_argument("--bitrate", help="Audio bitrate")

    m3u8_parser = subparsers.add_parser("m3u8", help="Download m3u8 video stream")
    m3u8_parser.add_argument("url", help="URL of the m3u8 file")
    m3u8_parser.add_argument("--output", help="Output file name without extension")
    m3u8_parser.add_argument(
        "--dir", default=os.getcwd(), help="Directory to save the output (default is current directory)"
    )
    m3u8_parser.add_argument("--vcodec", default="copy", help="Video codec")
    m3u8_parser.add_argument("--acodec", default="copy", help="Audio codec")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "video" or args.command == "audio":
        input_path = args.input
        input_files = []

        if os.path.isdir(input_path):
            media_type = "video" if args.command == "video" else "audio"
            input_files = list_media_files(input_path, media_type)
            if not input_files:
                print("[ERROR] No supported media files found in directory.", file=sys.stderr)
                sys.exit(1)
        elif os.path.isfile(input_path):
            input_files = [input_path]
        else:
            print(f"[ERROR] Invalid input: {input_path}", file=sys.stderr)
            sys.exit(1)

        if args.command == "video":
            process_inputs(input_files, convert_video, args)
        elif args.command == "audio":
            process_inputs(input_files, convert_audio, args)
    elif args.command == "m3u8":
        download_m3u8(args.url, args)


if __name__ == "__main__":
    main()
