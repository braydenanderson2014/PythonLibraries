#!/usr/bin/env python3
"""
Media File Organizer
Organizes torrented media files by:
- Moving movies up one level and renaming to folder name
- Renaming TV show episodes to keep only S##E## format
Run this script in the parent directory of your media folders.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple

# Video file extensions to look for
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.webm'}

# TV show pattern: matches S01E02 or s01e02 format
TV_PATTERN = re.compile(r'([Ss]\d{2}[Ee]\d{2})', re.IGNORECASE)


def is_tv_show(folder_name: str, files: list) -> bool:
    """
    Determine if a folder is a TV show by checking for season/episode patterns.
    """
    # Check folder name for S##E## pattern
    if TV_PATTERN.search(folder_name):
        return True
    
    # Check filenames for S##E## pattern
    for file in files:
        if TV_PATTERN.search(file):
            return True
    
    return False


def extract_season_episode(filename: str) -> Optional[str]:
    """
    Extract season and episode number from filename (S01E02 format).
    Returns the S##E## part if found, None otherwise.
    """
    match = TV_PATTERN.search(filename)
    if match:
        return match.group(1).upper()  # Return as S##E## format
    return None


def get_video_files(folder_path: Path) -> list:
    """
    Get all video files in a folder.
    """
    return [f for f in os.listdir(folder_path) 
            if os.path.isfile(os.path.join(folder_path, f)) 
            and Path(f).suffix.lower() in VIDEO_EXTENSIONS]


def organize_movies(base_path: Path) -> Tuple[int, int]:
    """
    Organize movie folders by moving video files up one level.
    Returns tuple of (movies_processed, errors)
    """
    movies_processed = 0
    errors = 0
    
    for folder_name in os.listdir(base_path):
        folder_path = base_path / folder_name
        
        # Skip if not a directory
        if not os.path.isdir(folder_path):
            continue
        
        video_files = get_video_files(folder_path)
        
        # Skip if no video files or if it's a TV show
        if not video_files or is_tv_show(folder_name, video_files):
            continue
        
        # Process movie
        try:
            print(f"Processing movie: {folder_name}")
            
            for video_file in video_files:
                old_path = folder_path / video_file
                # Get the video extension from the original file
                file_ext = Path(video_file).suffix
                new_filename = f"{folder_name}{file_ext}"
                new_path = base_path / new_filename
                
                # Handle file name conflicts
                if new_path.exists():
                    counter = 1
                    name_parts = folder_name.rsplit('.', 1) if '.' in folder_name else (folder_name, '')
                    while new_path.exists():
                        new_filename = f"{name_parts[0]}_{counter}{file_ext}"
                        new_path = base_path / new_filename
                        counter += 1
                
                print(f"  Moving: {video_file} -> {new_filename}")
                shutil.move(str(old_path), str(new_path))
            
            # Delete the now-empty folder
            try:
                os.rmdir(folder_path)
                print(f"  Removed empty folder: {folder_name}")
            except OSError:
                print(f"  Warning: Could not remove folder {folder_name} (may not be empty)")
            
            movies_processed += 1
            
        except Exception as e:
            print(f"  ERROR processing {folder_name}: {e}")
            errors += 1
    
    return movies_processed, errors


def organize_tv_shows(base_path: Path) -> Tuple[int, int]:
    """
    Organize TV show folders by renaming files to keep only S##E## format.
    Recursively scans through subdirectories (e.g., TV Shows > Show Name > Season > Files)
    Returns tuple of (shows_processed, files_renamed)
    """
    files_renamed = 0
    
    # Recursively walk through all directories
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)
        
        # Look for video files in the current directory
        video_files = [f for f in files if Path(f).suffix.lower() in VIDEO_EXTENSIONS]
        
        if not video_files:
            continue
        
        # Check if this directory or any of its files indicate it's a TV show
        dir_name = os.path.basename(root)
        if not is_tv_show(dir_name, video_files):
            continue
        
        print(f"Processing TV show files in: {root}")
        
        for video_file in video_files:
            season_episode = extract_season_episode(video_file)
            
            if not season_episode:
                print(f"  Skipping (no S##E## found): {video_file}")
                continue
            
            try:
                old_path = root_path / video_file
                file_ext = Path(video_file).suffix
                
                # Create new filename with just S##E## and extension
                new_filename = f"{season_episode}{file_ext}"
                new_path = root_path / new_filename
                
                # Handle file name conflicts
                if new_path.exists() and new_path != old_path:
                    counter = 1
                    while (root_path / f"{season_episode}_{counter}{file_ext}").exists():
                        counter += 1
                    new_filename = f"{season_episode}_{counter}{file_ext}"
                    new_path = root_path / new_filename
                
                if new_path != old_path:  # Only rename if name actually changes
                    print(f"  Renaming: {video_file} -> {new_filename}")
                    os.rename(str(old_path), str(new_path))
                    files_renamed += 1
                
            except Exception as e:
                print(f"  ERROR renaming {video_file}: {e}")
    
    return files_renamed


def main():
    """
    Main function to orchestrate the organization process.
    """
    print("=" * 60)
    print("Media File Organizer")
    print("=" * 60)
    
    # Get the current directory
    base_path = Path.cwd()
    print(f"\nScanning directory: {base_path}\n")
    
    # Organize movies
    print("ORGANIZING MOVIES")
    print("-" * 60)
    movies_processed, movie_errors = organize_movies(base_path)
    print(f"Movies processed: {movies_processed}, Errors: {movie_errors}\n")
    
    # Organize TV shows
    print("ORGANIZING TV SHOWS")
    print("-" * 60)
    files_renamed = organize_tv_shows(base_path)
    print(f"TV show files renamed: {files_renamed}\n")
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Movies moved: {movies_processed}")
    print(f"TV show files renamed: {files_renamed}")
    print(f"Errors encountered: {movie_errors}")
    print("\nOrganization complete!")


if __name__ == "__main__":
    main()
