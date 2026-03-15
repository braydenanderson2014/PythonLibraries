#!/usr/bin/env python3
"""
Media Metadata Repair Tool
Analyzes and repairs corrupted metadata in mkv/mp4 files using FFmpeg.
Runs in the current directory and processes all media files found.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
import shutil

# Video file extensions to process
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.webm'}

# Backup directory for original files
BACKUP_DIR = Path.cwd() / "media_backups"


def check_ffmpeg() -> bool:
    """
    Check if FFmpeg and ffprobe are installed.
    """
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_file_info(file_path: Path) -> Optional[Dict]:
    """
    Use ffprobe to get detailed information about a media file.
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as je:
                print(f"  Error parsing JSON: {je}")
                return None
        else:
            if result.stderr:
                print(f"  ffprobe error: {result.stderr[:200]}")
            else:
                print(f"  ffprobe failed (code: {result.returncode})")
            return None
    except subprocess.TimeoutExpired:
        print(f"  Error: File analysis timed out")
        return None
    except Exception as e:
        print(f"  Error analyzing file: {e}")
        return None


def check_metadata_issues(file_info: Dict) -> List[str]:
    """
    Always attempt repair since torrent files often have issues even if readable.
    Returns a list with a placeholder so we know to attempt repair.
    """
    # Always return an issue so we attempt repair - ffprobe failing is itself an issue
    return ["Attempting container rebuild"]


def repair_file(file_path: Path, backup: bool = True) -> bool:
    """
    Repair a media file using aggressive FFmpeg options to handle corrupted files.
    Attempts multiple strategies to rebuild the container.
    """
    temp_file = None
    try:
        # Create backup if requested
        if backup:
            BACKUP_DIR.mkdir(exist_ok=True)
            backup_path = BACKUP_DIR / file_path.name
            
            # Skip if backup already exists
            if backup_path.exists():
                print(f"  Backup already exists, skipping backup")
            else:
                print(f"  Creating backup: {backup_path}")
                shutil.copy2(str(file_path), str(backup_path))
        
        # Create temp file for output
        temp_file = file_path.parent / f"{file_path.stem}_repair_temp{file_path.suffix}"
        
        print(f"  Rebuilding container...")
        
        # Try with aggressive error handling and PTS generation
        result = subprocess.run(
            [
                'ffmpeg',
                '-fflags', '+genpts',  # Generate presentation timestamps
                '-err_detect', 'ignore_err',  # Ignore errors and continue
                '-i', str(file_path),
                '-c', 'copy',  # Copy all streams without re-encoding
                '-y',  # Overwrite output
                '-v', 'quiet',  # Suppress verbose output
                '-hide_banner',
                str(temp_file)
            ],
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )
        
        if result.returncode == 0 and temp_file.exists():
            temp_size = os.path.getsize(temp_file)
            if temp_size > 1000:  # At least 1KB
                original_size = os.path.getsize(file_path)
                print(f"  Original: {original_size / (1024**2):.1f} MB -> Repaired: {temp_size / (1024**2):.1f} MB")
                # Replace original with repaired version
                os.remove(str(file_path))
                os.rename(str(temp_file), str(file_path))
                return True
            else:
                print(f"  Error: Output file too small ({temp_size} bytes)")
                if temp_file.exists():
                    os.remove(str(temp_file))
                return False
        else:
            # Even if return code is not 0, ffmpeg might have created a valid file
            if temp_file.exists() and os.path.getsize(temp_file) > 1000:
                print(f"  FFmpeg reported error but output file exists, attempting to use it...")
                try:
                    os.remove(str(file_path))
                    os.rename(str(temp_file), str(file_path))
                    return True
                except Exception as e:
                    print(f"  Could not replace original: {e}")
                    return False
            
            print(f"  Error during repair (code: {result.returncode})")
            if result.stderr:
                # Show last 500 chars of stderr
                stderr_lines = result.stderr.split('\n')
                for line in stderr_lines[-5:]:
                    if line.strip():
                        print(f"  {line}")
            if temp_file and temp_file.exists():
                os.remove(str(temp_file))
            return False
            
    except subprocess.TimeoutExpired:
        print(f"  Error: Repair timed out (file too large or unreadable)")
        if temp_file and temp_file.exists():
            os.remove(str(temp_file))
        return False
    except Exception as e:
        print(f"  Error during repair: {e}")
        if temp_file and temp_file.exists():
            os.remove(str(temp_file))
        return False


def validate_repair(file_path: Path) -> bool:
    """
    Validate that a file was repaired successfully.
    """
    file_info = get_file_info(file_path)
    if not file_info:
        return False
    
    # Check if file has valid streams and format
    if 'streams' not in file_info or 'format' not in file_info:
        return False
    
    return len(file_info['streams']) > 0


def main():
    """
    Main function to scan and repair all media files in the current directory.
    """
    print("=" * 60)
    print("Media Metadata Repair Tool")
    print("=" * 60)
    
    # Check for FFmpeg
    if not check_ffmpeg():
        print("\nERROR: FFmpeg or ffprobe not found!")
        print("Please install FFmpeg from: https://ffmpeg.org/download.html")
        print("\nOn Windows, you can also install via:")
        print("  choco install ffmpeg")
        print("  or")
        print("  scoop install ffmpeg")
        return
    
    base_path = Path.cwd()
    print(f"\nScanning directory: {base_path}\n")
    
    # Find all media files in current directory
    media_files = [
        f for f in os.listdir(base_path)
        if os.path.isfile(os.path.join(base_path, f))
        and Path(f).suffix.lower() in VIDEO_EXTENSIONS
    ]
    
    if not media_files:
        print("No media files found in current directory.")
        return
    
    print(f"Found {len(media_files)} media file(s)\n")
    
    # Statistics
    analyzed = 0
    issues_found = 0
    repaired = 0
    failed = 0
    
    # Process each file
    for filename in media_files:
        file_path = base_path / filename
        file_size_gb = os.path.getsize(file_path) / (1024**3)
        
        print(f"Processing: {filename}")
        print(f"  File size: {file_size_gb:.2f} GB")
        
        try:
            # Skip files that appear to be incomplete (0 or very small)
            if file_size_gb < 0.01:
                print(f"  ⚠ Skipping - file appears to be incomplete or corrupted (too small)")
                failed += 1
                print()
                continue
            
            # Attempt repair directly without analysis
            print(f"  Attempting repair...")
            if repair_file(file_path, backup=True):
                print(f"  ✓ Successfully repaired")
                repaired += 1
            else:
                print(f"  ✗ Repair failed")
                failed += 1
        
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1
        
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed: {len(media_files)}")
    print(f"Files successfully repaired: {repaired}")
    print(f"Repair failures: {failed}")
    
    if BACKUP_DIR.exists():
        backup_count = len(os.listdir(BACKUP_DIR))
        print(f"\nBackups created: {backup_count}")
        print(f"Backup directory: {BACKUP_DIR}")
    
    print("\nRepair process complete!")


if __name__ == "__main__":
    main()
