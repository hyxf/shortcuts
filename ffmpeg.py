#!/usr/bin/env python3
import os
import subprocess
import argparse
import sys
from typing import List, Optional


def check_ffmpeg() -> bool:
    """
    Check if ffmpeg is available in the system.

    Returns:
        bool: True if ffmpeg is available, False otherwise
    """
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def generate_output_path(input_path: str, output_ext: str = ".mp4", output_name: Optional[str] = None) -> str:
    """
    Generate a unique output file path to avoid overwriting existing files.

    Args:
        input_path: Path to the input file
        output_ext: Output file extension
        output_name: Optional specific output filename (without extension)

    Returns:
        str: Generated unique output path
    """
    # Ensure extension format is correct
    if not output_ext.startswith("."):
        output_ext = f".{output_ext}"

    # Get directory
    input_dir = os.path.dirname(input_path) or "."

    # Use specified name or derive from input path
    if output_name:
        base_name = output_name
    else:
        base_name = os.path.splitext(os.path.basename(input_path))[0]

    # Generate unique filename
    index = 0
    while True:
        suffix = f"_{index}" if index > 0 else ""
        output_filename = f"{base_name}{suffix}{output_ext}"
        output_path = os.path.join(input_dir, output_filename)
        if not os.path.exists(output_path):
            return output_path
        index += 1


def run_ffmpeg(cmd: List[str]) -> bool:
    """
    Run the given ffmpeg command.

    Args:
        cmd: List of command arguments

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"[INFO] Running command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(f"[SUCCESS] Conversion completed: {cmd[-1]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg conversion failed: {e}", file=sys.stderr)
        return False


def convert_with_ffmpeg(
    input_path: str, output_ext: str, video_codec: str, audio_codec: str, output_name: Optional[str] = None
) -> Optional[str]:
    """
    Converts a video using ffmpeg with specified codecs.

    Args:
        input_path: Path to the input video file
        output_ext: Output file extension
        video_codec: Video codec to use (ffmpeg -c:v parameter)
        audio_codec: Audio codec to use (ffmpeg -c:a parameter)
        output_name: Optional specific output filename (without extension)

    Returns:
        str: Path to the output file if successful, None otherwise
    """
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"[ERROR] Input file does not exist: {input_path}", file=sys.stderr)
        return None

    # Generate output path
    output_path = generate_output_path(input_path, output_ext, output_name)

    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", input_path, "-c:v", video_codec, "-c:a", audio_codec, output_path]

    # Run the command
    if run_ffmpeg(cmd):
        return output_path
    return None


def main():
    """Main entry point of the program"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="Convert video files using ffmpeg with codec options.")
    parser.add_argument("input", help="Path to the input video file")
    parser.add_argument("--ext", default=".mp4", help="Output file extension (default: .mp4)")
    parser.add_argument("--vcodec", default="libx264", help="Video codec (default: libx264)")
    parser.add_argument("--acodec", default="aac", help="Audio codec (default: copy)")
    parser.add_argument("--output", help="Output filename without extension (default: same as input)")
    args = parser.parse_args()

    # Check if ffmpeg is available
    if not check_ffmpeg():
        print("[ERROR] ffmpeg is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)

    try:
        # Execute conversion with specified codecs and output name
        output_path = convert_with_ffmpeg(args.input, args.ext, args.vcodec, args.acodec, args.output)

        # Handle result
        if output_path:
            print(f"[SUCCESS] File saved to: {output_path}")
            # Output file information
            if os.path.exists(output_path):
                input_size = os.path.getsize(args.input) / 1024 / 1024  # MB
                output_size = os.path.getsize(output_path) / 1024 / 1024  # MB
                print(f"[INFO] Input file size: {input_size:.2f} MB")
                print(f"[INFO] Output file size: {output_size:.2f} MB")
                change_pct = ((output_size / input_size) - 1) * 100 if input_size > 0 else 0
                print(f"[INFO] Size change: {output_size - input_size:.2f} MB ({change_pct:.1f}%)")
        else:
            print("[ERROR] Conversion failed", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
