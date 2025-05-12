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
        subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            check=True
        )
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
        print(f"[SUCCESS] Completed: {cmd[-1]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] ffmpeg command failed: {e}", file=sys.stderr)
        return False


def print_file_info(input_path: str, output_path: str) -> None:
    """
    Print information about input and output files.
    
    Args:
        input_path: Path to the input file
        output_path: Path to the output file
    """
    if os.path.exists(output_path):
        input_size = os.path.getsize(input_path) / 1024 / 1024  # MB
        output_size = os.path.getsize(output_path) / 1024 / 1024  # MB
        print(f"[INFO] Input file size: {input_size:.2f} MB")
        print(f"[INFO] Output file size: {output_size:.2f} MB")
        if input_size > 0:
            change_pct = ((output_size / input_size) - 1) * 100
            print(f"[INFO] Size change: {output_size - input_size:.2f} MB ({change_pct:.1f}%)")


def convert_video(args):
    """
    Convert video using specified codecs.
    
    Args:
        args: Command line arguments
    """
    # Generate output path
    output_path = generate_output_path(args.input, args.ext, args.output)
    
    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", args.input, "-c:v", args.vcodec, "-c:a", args.acodec, output_path]
    
    # Run the command
    if run_ffmpeg(cmd):
        print(f"[SUCCESS] Video saved to: {output_path}")
        print_file_info(args.input, output_path)
        return True
    return False


def convert_audio(args):
    """
    Convert audio format.
    
    Args:
        args: Command line arguments
    """
    # Generate output path
    output_path = generate_output_path(args.input, args.ext, args.output)
    
    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", args.input, "-c:a", args.acodec]
    
    # Add bitrate if specified
    if args.bitrate:
        cmd.extend(["-b:a", args.bitrate])
    
    # Add output path
    cmd.append(output_path)
    
    # Run the command
    if run_ffmpeg(cmd):
        print(f"[SUCCESS] Audio saved to: {output_path}")
        print_file_info(args.input, output_path)
        return True
    return False


def extract_audio(args):
    """
    Extract audio from video file.
    
    Args:
        args: Command line arguments
    """
    # Generate output path
    output_path = generate_output_path(args.input, args.ext, args.output)
    
    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", args.input, "-vn"]  # -vn means no video
    
    # Add codec
    cmd.extend(["-c:a", args.acodec])
    
    # Add bitrate if specified
    if args.bitrate:
        cmd.extend(["-b:a", args.bitrate])
    
    # Add output path
    cmd.append(output_path)
    
    # Run the command
    if run_ffmpeg(cmd):
        print(f"[SUCCESS] Extracted audio saved to: {output_path}")
        print_file_info(args.input, output_path)
        return True
    return False


def main():
    """Main entry point of the program"""
    # Check if ffmpeg is available
    if not check_ffmpeg():
        print("[ERROR] ffmpeg is not installed or not in PATH", file=sys.stderr)
        sys.exit(1)
    
    # Create main parser
    parser = argparse.ArgumentParser(
        description="Media conversion tools using ffmpeg."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Video conversion command
    video_parser = subparsers.add_parser("video", help="Convert video")
    video_parser.add_argument("input", help="Path to the input video file")
    video_parser.add_argument("--ext", default=".mp4", help="Output file extension (default: .mp4)")
    video_parser.add_argument("--vcodec", default="libx264", help="Video codec (default: libx264)")
    video_parser.add_argument("--acodec", default="aac", help="Audio codec (default: aac)")
    video_parser.add_argument("--output", help="Output filename without extension (default: same as input)")
    
    # Audio conversion command
    audio_parser = subparsers.add_parser("audio", help="Convert audio")
    audio_parser.add_argument("input", help="Path to the input audio file")
    audio_parser.add_argument("--ext", default=".m4a", help="Output file extension (default: .m4a)")
    audio_parser.add_argument("--acodec", default="aac", help="Audio codec (default: aac)")
    audio_parser.add_argument("--bitrate", default="192k", help="Audio bitrate (default: 192k)")
    audio_parser.add_argument("--output", help="Output filename without extension (default: same as input)")
    
    # Extract audio command
    extract_parser = subparsers.add_parser("extract", help="Extract audio from video")
    extract_parser.add_argument("input", help="Path to the input video file")
    extract_parser.add_argument("--ext", default=".m4a", help="Output file extension (default: .m4a)")
    extract_parser.add_argument("--acodec", default="aac", help="Audio codec (default: aac)")
    extract_parser.add_argument("--bitrate", default="192k", help="Audio bitrate (default: 192k)")
    extract_parser.add_argument("--output", help="Output filename without extension (default: same as input)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle legacy mode (no subcommand provided) - default to video conversion
    if args.command is None and hasattr(args, 'input'):
        args.command = "video"
    
    # Execute requested command
    try:
        if args.command == "video":
            if not os.path.exists(args.input):
                print(f"[ERROR] Input file does not exist: {args.input}", file=sys.stderr)
                sys.exit(1)
            success = convert_video(args)
        elif args.command == "audio":
            if not os.path.exists(args.input):
                print(f"[ERROR] Input file does not exist: {args.input}", file=sys.stderr)
                sys.exit(1)
            success = convert_audio(args)
        elif args.command == "extract":
            if not os.path.exists(args.input):
                print(f"[ERROR] Input file does not exist: {args.input}", file=sys.stderr)
                sys.exit(1)
            success = extract_audio(args)
        else:
            parser.print_help()
            sys.exit(0)
        
        sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()