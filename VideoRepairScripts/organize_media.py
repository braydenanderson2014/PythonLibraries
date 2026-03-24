#!/usr/bin/env python3
"""Supercharged media organizer.

Features:
- JSON config support for cleanup and naming rules.
- Online title lookup (no API keys required) for:
  - Movies via iTunes Search API.
  - TV episode names via TVMaze API.
- Preservation of filename traits (resolution/source/codec/audio/release group).
- CLI-friendly operation with dry-run mode and JSON summary output.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".flv",
    ".wmv",
    ".m4v",
    ".webm",
}

INVALID_FILENAME_CHARS = re.compile(r"[<>:\"/\\|?*]+")


def default_config() -> Dict[str, Any]:
    return {
        "dry_run": False,
        "organize_movies": True,
        "organize_tv": True,
        "recursive_tv_scan": True,
        "cleanup_empty_movie_folders": True,
        "online_lookup": {
            "enabled": False,
            "timeout_seconds": 8,
            "movie_provider": "itunes",
            "tv_provider": "tvmaze",
            "include_episode_title": False,
        },
        "preserve": {
            "enabled": True,
            "fields": [],
            "separator": " ",
            "style": "brackets",
            "extra_regex": [],
        },
        "movie_name": {
            "template": "{title}{trait_suffix}",
            "normalize_separators": True,
            "strip_bracketed": True,
            "cutoff_tokens": [
                r"\b2160p\b",
                r"\b1080p\b",
                r"\b720p\b",
                r"\bWEB[-_. ]?DL\b",
                r"\bWEB[-_. ]?Rip\b",
                r"\bBluRay\b",
                r"\bBRRip\b",
                r"\bx264\b",
                r"\bx265\b",
                r"\bHEVC\b",
                r"\bAAC\b",
                r"\bDDP?5\.1\b",
                r"\bYTS\b",
                r"\bRARBG\b",
            ],
            "cleanup_regex": [
                {"pattern": r"[-_]+", "replace": " "},
            ],
        },
        "tv_name": {
            "template": "{clean_name} - {season_episode}{episode_title_suffix}{trait_suffix}",
            "normalize_separators": True,
            "strip_bracketed": True,
            "patterns": [
                {
                    "pattern": r"(?i)S(?P<season>\d{1,2})E(?P<episode>\d{1,3})",
                    "season_group": "season",
                    "episode_group": "episode",
                },
                {
                    "pattern": r"(?i)(?P<season>\d{1,2})x(?P<episode>\d{1,3})",
                    "season_group": "season",
                    "episode_group": "episode",
                },
                {
                    "pattern": r"(?i)Season[ ._-]?(?P<season>\d{1,2})[ ._-]*Episode[ ._-]?(?P<episode>\d{1,3})",
                    "season_group": "season",
                    "episode_group": "episode",
                },
            ],
            "cutoff_tokens": [
                r"\b2160p\b",
                r"\b1080p\b",
                r"\b720p\b",
                r"\bWEB[-_. ]?DL\b",
                r"\bWEB[-_. ]?Rip\b",
                r"\bBluRay\b",
                r"\bBRRip\b",
                r"\bx264\b",
                r"\bx265\b",
                r"\bHEVC\b",
                r"\bAAC\b",
                r"\bDDP?5\.1\b",
                r"\bYTS\b",
                r"\bRARBG\b",
            ],
            "cleanup_regex": [
                {"pattern": r"[-_]+", "replace": " "},
            ],
        },
    }


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_json_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}

    config_path = Path(path).expanduser().resolve()
    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Config root must be a JSON object: {config_path}")

    return payload


def sanitize_filename(name: str) -> str:
    cleaned = INVALID_FILENAME_CHARS.sub(" ", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "unnamed"


def clean_media_name(value: str, rules: Dict[str, Any]) -> str:
    cleaned = value

    if bool(rules.get("normalize_separators", False)):
        cleaned = re.sub(r"[._]+", " ", cleaned)

    if bool(rules.get("strip_bracketed", False)):
        cleaned = re.sub(r"\[[^\]]*\]", " ", cleaned)
        cleaned = re.sub(r"\([^\)]*\)", " ", cleaned)
        cleaned = re.sub(r"\{[^\}]*\}", " ", cleaned)

    cutoff_tokens = rules.get("cutoff_tokens", [])
    if isinstance(cutoff_tokens, list) and cutoff_tokens:
        cutoff_index = len(cleaned)
        for token in cutoff_tokens:
            if not isinstance(token, str) or not token.strip():
                continue
            token_text = token.strip()
            try:
                match = re.search(token_text, cleaned, re.IGNORECASE)
            except re.error:
                match = re.search(re.escape(token_text), cleaned, re.IGNORECASE)
            if match and match.start() < cutoff_index:
                cutoff_index = match.start()
        cleaned = cleaned[:cutoff_index]

    cleanup_regex = rules.get("cleanup_regex", [])
    if isinstance(cleanup_regex, list):
        for entry in cleanup_regex:
            if not isinstance(entry, dict):
                continue
            pattern = entry.get("pattern")
            replace = entry.get("replace", "")
            if not isinstance(pattern, str) or not pattern:
                continue
            if not isinstance(replace, str):
                replace = str(replace)
            try:
                cleaned = re.sub(pattern, replace, cleaned)
            except re.error:
                continue

    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-")
    return cleaned or value.strip()


def extract_episode_info(file_stem: str, tv_rules: Dict[str, Any]) -> Optional[Dict[str, int]]:
    configured_patterns = tv_rules.get("patterns", [])
    pattern_entries: List[Dict[str, Any]] = []

    if isinstance(configured_patterns, list):
        for entry in configured_patterns:
            if isinstance(entry, str):
                pattern_entries.append(
                    {
                        "pattern": entry,
                        "season_group": "season",
                        "episode_group": "episode",
                    }
                )
            elif isinstance(entry, dict):
                pattern_entries.append(
                    {
                        "pattern": entry.get("pattern"),
                        "season_group": entry.get("season_group", "season"),
                        "episode_group": entry.get("episode_group", "episode"),
                    }
                )

    if not pattern_entries:
        pattern_entries = [{"pattern": r"([Ss]\d{1,2}[Ee]\d{1,3})", "season_group": None, "episode_group": None}]

    for entry in pattern_entries:
        pattern = entry.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            continue

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            continue

        match = regex.search(file_stem)
        if not match:
            continue

        season_group = entry.get("season_group")
        episode_group = entry.get("episode_group")

        season: Optional[int] = None
        episode: Optional[int] = None

        if isinstance(season_group, str) and isinstance(episode_group, str):
            try:
                season = int(match.group(season_group))
                episode = int(match.group(episode_group))
            except (IndexError, KeyError, TypeError, ValueError):
                season = None
                episode = None

        if season is None or episode is None:
            full_match = match.group(0)
            sxe = re.search(r"[Ss](\d{1,2})[Ee](\d{1,3})", full_match)
            if sxe:
                season = int(sxe.group(1))
                episode = int(sxe.group(2))
            elif match.lastindex and match.lastindex >= 2:
                try:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                except (TypeError, ValueError):
                    season = None
                    episode = None

        if season is None or episode is None:
            continue

        return {"season": season, "episode": episode, "match_start": int(match.start())}

    return None


def infer_traits(text: str) -> Dict[str, str]:
    traits: Dict[str, str] = {}
    patterns = {
        "resolution": r"\b(2160p|1080p|720p|480p)\b",
        "source": r"\b(WEB[-_. ]?DL|WEB[-_. ]?Rip|BluRay|BRRip|DVDRip|HDRip)\b",
        "codec": r"\b(x264|x265|h\.264|h\.265|HEVC|AV1)\b",
        "audio": r"\b(AAC|DDP?5\.1|DTS(?:[-_. ]?HD)?|TRUEHD|ATMOS)\b",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            traits[key] = match.group(1).replace(".", "").replace("_", " ").strip()

    group_match = re.search(r"-([A-Za-z0-9]{2,20})$", text)
    if group_match:
        traits["release_group"] = group_match.group(1)

    return traits


def render_trait_suffix(filename_stem: str, preserve_cfg: Dict[str, Any]) -> str:
    if not bool(preserve_cfg.get("enabled", False)):
        return ""

    fields = preserve_cfg.get("fields", [])
    if not isinstance(fields, list) or not fields:
        return ""

    trait_map = infer_traits(filename_stem)
    values: List[str] = []
    for key in fields:
        if isinstance(key, str) and key in trait_map:
            values.append(trait_map[key])

    extra_regex = preserve_cfg.get("extra_regex", [])
    if isinstance(extra_regex, list):
        for pattern in extra_regex:
            if not isinstance(pattern, str) or not pattern:
                continue
            try:
                match = re.search(pattern, filename_stem, re.IGNORECASE)
            except re.error:
                continue
            if match:
                values.append(match.group(0))

    if not values:
        return ""

    separator = str(preserve_cfg.get("separator", " "))
    joined = separator.join(dict.fromkeys(values))
    style = str(preserve_cfg.get("style", "brackets")).lower()

    if style == "plain":
        return f" {joined}"
    if style == "dash":
        return f" - {joined}"
    return f" [{joined}]"


def find_year(text: str) -> Optional[int]:
    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if not match:
        return None
    return int(match.group(1))


def http_json_get(url: str, timeout_seconds: int) -> Optional[Dict[str, Any]]:
    request = urllib.request.Request(url, headers={"User-Agent": "media-organizer/2.0"})
    try:
        with urllib.request.urlopen(request, timeout=max(timeout_seconds, 1)) as response:
            content = response.read().decode("utf-8", errors="replace")
            payload = json.loads(content)
            if isinstance(payload, dict):
                return payload
            return {"_list": payload} if isinstance(payload, list) else None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def lookup_movie_title_itunes(clean_name: str, year: Optional[int], timeout_seconds: int) -> Optional[Dict[str, Any]]:
    params = {
        "term": clean_name,
        "entity": "movie",
        "limit": "8",
    }
    url = "https://itunes.apple.com/search?" + urllib.parse.urlencode(params)
    payload = http_json_get(url, timeout_seconds)
    if not payload:
        return None

    results = payload.get("results", [])
    if not isinstance(results, list) or not results:
        return None

    selected: Optional[Dict[str, Any]] = None
    if year is not None:
        for item in results:
            if not isinstance(item, dict):
                continue
            release_date = str(item.get("releaseDate", ""))
            item_year_match = re.search(r"\b(\d{4})\b", release_date)
            if item_year_match and int(item_year_match.group(1)) == year:
                selected = item
                break

    if selected is None:
        selected = results[0] if isinstance(results[0], dict) else None

    if not selected:
        return None

    movie_title = str(selected.get("trackName", "")).strip()
    if not movie_title:
        return None

    release_date = str(selected.get("releaseDate", ""))
    year_match = re.search(r"\b(\d{4})\b", release_date)
    found_year = int(year_match.group(1)) if year_match else None
    return {"title": movie_title, "year": found_year}


def lookup_tv_episode_title_tvmaze(show_name: str, season: int, episode: int, timeout_seconds: int) -> Optional[str]:
    search_params = urllib.parse.urlencode({"q": show_name})
    search_url = f"https://api.tvmaze.com/search/shows?{search_params}"
    search_payload = http_json_get(search_url, timeout_seconds)
    if not search_payload:
        return None

    raw_items = search_payload.get("_list", [])
    if not isinstance(raw_items, list) or not raw_items:
        return None

    selected_show_id: Optional[int] = None
    for item in raw_items[:5]:
        if not isinstance(item, dict):
            continue
        show = item.get("show")
        if isinstance(show, dict) and isinstance(show.get("id"), int):
            selected_show_id = show["id"]
            break

    if selected_show_id is None:
        return None

    episode_url = f"https://api.tvmaze.com/shows/{selected_show_id}/episodebynumber?season={season}&number={episode}"
    episode_payload = http_json_get(episode_url, timeout_seconds)
    if not episode_payload:
        return None

    title = episode_payload.get("name")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return None


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def collect_video_files(folder_path: Path) -> List[Path]:
    videos: List[Path] = []
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
            videos.append(item)
    return videos


def render_template_with_fallback(template: str, values: Dict[str, Any], fallback: str) -> str:
    try:
        rendered = template.format(**values)
    except Exception:
        rendered = fallback

    rendered = re.sub(r"\s+", " ", rendered).strip(" ._-")
    return rendered or fallback


@dataclass
class Summary:
    base_path: str
    dry_run: bool
    scanned: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    movies_processed: int = 0
    tv_files_renamed: int = 0
    actions: List[Dict[str, Any]] = field(default_factory=list)

    def add_action(self, action: Dict[str, Any]) -> None:
        self.actions.append(action)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_path": self.base_path,
            "dry_run": self.dry_run,
            "scanned": self.scanned,
            "processed": self.processed,
            "failed": self.failed,
            "skipped": self.skipped,
            "movies_processed": self.movies_processed,
            "tv_files_renamed": self.tv_files_renamed,
            "actions": self.actions,
        }


class Organizer:
    def __init__(self, base_path: Path, config: Dict[str, Any], verbose: bool = True):
        self.base_path = base_path
        self.config = config
        self.verbose = verbose
        self.summary = Summary(base_path=str(base_path), dry_run=bool(config.get("dry_run", False)))
        self.movie_lookup_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self.tv_lookup_cache: Dict[str, Optional[str]] = {}

    def log(self, message: str) -> None:
        if self.verbose:
            print(message)

    def is_tv_candidate(self, folder_name: str, video_files: List[Path]) -> bool:
        tv_rules = self.config.get("tv_name", {})
        if extract_episode_info(folder_name, tv_rules):
            return True
        for video in video_files:
            if extract_episode_info(video.stem, tv_rules):
                return True
        return False

    def maybe_lookup_movie(self, clean_title: str, year: Optional[int]) -> Dict[str, Any]:
        online_cfg = self.config.get("online_lookup", {})
        if not isinstance(online_cfg, dict) or not bool(online_cfg.get("enabled", False)):
            return {"title": clean_title, "year": year}

        provider = str(online_cfg.get("movie_provider", "itunes")).lower()
        timeout_seconds = int(online_cfg.get("timeout_seconds", 8) or 8)
        if provider != "itunes":
            return {"title": clean_title, "year": year}

        cache_key = f"{clean_title.lower()}|{year}"
        if cache_key in self.movie_lookup_cache:
            cached = self.movie_lookup_cache[cache_key]
            return cached if cached else {"title": clean_title, "year": year}

        looked_up = lookup_movie_title_itunes(clean_title, year, timeout_seconds)
        self.movie_lookup_cache[cache_key] = looked_up
        if looked_up:
            self.log(f"Online movie match: '{clean_title}' -> '{looked_up['title']}'")
            return looked_up
        return {"title": clean_title, "year": year}

    def maybe_lookup_episode_title(self, show_name: str, season: int, episode: int) -> Optional[str]:
        online_cfg = self.config.get("online_lookup", {})
        if not isinstance(online_cfg, dict) or not bool(online_cfg.get("enabled", False)):
            return None
        if not bool(online_cfg.get("include_episode_title", False)):
            return None

        provider = str(online_cfg.get("tv_provider", "tvmaze")).lower()
        timeout_seconds = int(online_cfg.get("timeout_seconds", 8) or 8)
        if provider != "tvmaze":
            return None

        cache_key = f"{show_name.lower()}|{season}|{episode}"
        if cache_key in self.tv_lookup_cache:
            return self.tv_lookup_cache[cache_key]

        title = lookup_tv_episode_title_tvmaze(show_name, season, episode, timeout_seconds)
        self.tv_lookup_cache[cache_key] = title
        if title:
            self.log(f"Online TV match: {show_name} S{season:02d}E{episode:02d} -> {title}")
        return title

    def organize_movies(self) -> None:
        if not bool(self.config.get("organize_movies", True)):
            return

        movie_rules = self.config.get("movie_name", {})
        preserve_cfg = self.config.get("preserve", {})
        movie_template = str(movie_rules.get("template", "{title}{trait_suffix}"))
        dry_run = bool(self.config.get("dry_run", False))

        for subfolder in self.base_path.iterdir():
            if not subfolder.is_dir():
                continue

            video_files = collect_video_files(subfolder)
            if not video_files:
                continue

            if self.is_tv_candidate(subfolder.name, video_files):
                continue

            self.log(f"Processing movie folder: {subfolder.name}")
            folder_had_success = False
            for video_file in video_files:
                self.summary.scanned += 1
                try:
                    clean_title = clean_media_name(subfolder.name, movie_rules)
                    source_year = find_year(subfolder.name) or find_year(video_file.stem)
                    movie_result = self.maybe_lookup_movie(clean_title, source_year)

                    trait_suffix = render_trait_suffix(video_file.stem, preserve_cfg)
                    values = {
                        "title": sanitize_filename(str(movie_result.get("title", clean_title))),
                        "year": movie_result.get("year") or source_year or "",
                        "clean_name": sanitize_filename(clean_title),
                        "original_name": sanitize_filename(subfolder.name),
                        "trait_suffix": trait_suffix,
                    }
                    new_stem = render_template_with_fallback(movie_template, values, values["title"])
                    new_name = sanitize_filename(new_stem) + video_file.suffix

                    destination = unique_destination(self.base_path / new_name)
                    action = {
                        "type": "movie_move",
                        "source": str(video_file),
                        "destination": str(destination),
                        "dry_run": dry_run,
                    }

                    if dry_run:
                        self.log(f"[DRY-RUN] Move {video_file.name} -> {destination.name}")
                    else:
                        self.log(f"Move {video_file.name} -> {destination.name}")
                        shutil.move(str(video_file), str(destination))

                    self.summary.processed += 1
                    self.summary.add_action(action)
                    folder_had_success = True
                except Exception as exc:
                    self.summary.failed += 1
                    self.summary.add_action(
                        {
                            "type": "movie_move",
                            "source": str(video_file),
                            "status": "failed",
                            "reason": str(exc),
                        }
                    )

            if folder_had_success:
                self.summary.movies_processed += 1

            should_cleanup = bool(self.config.get("cleanup_empty_movie_folders", True))
            if should_cleanup and (dry_run or folder_had_success):
                try:
                    if not any(subfolder.iterdir()):
                        if dry_run:
                            self.log(f"[DRY-RUN] Remove empty folder: {subfolder}")
                        else:
                            subfolder.rmdir()
                except OSError:
                    pass

    def organize_tv(self) -> None:
        if not bool(self.config.get("organize_tv", True)):
            return

        tv_rules = self.config.get("tv_name", {})
        preserve_cfg = self.config.get("preserve", {})
        tv_template = str(tv_rules.get("template", "{season_episode}{trait_suffix}"))
        dry_run = bool(self.config.get("dry_run", False))
        recursive_scan = bool(self.config.get("recursive_tv_scan", True))

        if recursive_scan:
            walkers = os.walk(self.base_path)
        else:
            walkers = [(str(self.base_path), [], [p.name for p in self.base_path.iterdir() if p.is_file()])]

        for root, _, files in walkers:
            root_path = Path(root)
            video_files = [name for name in files if Path(name).suffix.lower() in VIDEO_EXTENSIONS]
            if not video_files:
                continue

            for video_name in video_files:
                self.summary.scanned += 1
                old_path = root_path / video_name
                stem = old_path.stem
                episode_info = extract_episode_info(stem, tv_rules)
                if not episode_info:
                    self.summary.skipped += 1
                    continue

                try:
                    season = int(episode_info["season"])
                    episode = int(episode_info["episode"])
                    season_episode = f"S{season:02d}E{episode:02d}"

                    prefix = stem[: int(episode_info["match_start"])].strip()
                    clean_source = prefix or root_path.name
                    clean_name = clean_media_name(clean_source, tv_rules)
                    episode_name = self.maybe_lookup_episode_title(clean_name, season, episode)
                    trait_suffix = render_trait_suffix(stem, preserve_cfg)
                    episode_title_suffix = f" - {sanitize_filename(episode_name)}" if episode_name else ""

                    values = {
                        "season": season,
                        "episode": episode,
                        "season_episode": season_episode,
                        "clean_name": sanitize_filename(clean_name),
                        "episode_name": sanitize_filename(episode_name) if episode_name else "",
                        "episode_title_suffix": episode_title_suffix,
                        "trait_suffix": trait_suffix,
                        "original_name": sanitize_filename(stem),
                    }
                    new_stem = render_template_with_fallback(tv_template, values, season_episode)
                    new_name = sanitize_filename(new_stem) + old_path.suffix

                    destination = unique_destination(root_path / new_name)
                    if destination == old_path:
                        self.summary.skipped += 1
                        continue

                    action = {
                        "type": "tv_rename",
                        "source": str(old_path),
                        "destination": str(destination),
                        "dry_run": dry_run,
                    }

                    if dry_run:
                        self.log(f"[DRY-RUN] Rename {old_path.name} -> {destination.name}")
                    else:
                        self.log(f"Rename {old_path.name} -> {destination.name}")
                        old_path.rename(destination)

                    self.summary.processed += 1
                    self.summary.tv_files_renamed += 1
                    self.summary.add_action(action)
                except Exception as exc:
                    self.summary.failed += 1
                    self.summary.add_action(
                        {
                            "type": "tv_rename",
                            "source": str(old_path),
                            "status": "failed",
                            "reason": str(exc),
                        }
                    )

    def run(self) -> Summary:
        self.organize_movies()
        self.organize_tv()
        return self.summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Supercharged media organizer with JSON config, online lookup, and automation-friendly CLI."
    )
    parser.add_argument("path", nargs="?", default=".", help="Base folder to organize (default: current directory)")
    parser.add_argument("--config", help="Path to JSON configuration file")
    parser.add_argument("--init-config", metavar="PATH", help="Write a starter config JSON to PATH and exit")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=None, help="Preview changes without moving/renaming files")
    parser.add_argument("--movies", action=argparse.BooleanOptionalAction, default=None, help="Enable or disable movie folder organization")
    parser.add_argument("--tv", action=argparse.BooleanOptionalAction, default=None, help="Enable or disable TV rename pass")
    parser.add_argument("--online-lookup", action=argparse.BooleanOptionalAction, default=None, help="Enable or disable online title lookup")
    parser.add_argument("--include-episode-title", action=argparse.BooleanOptionalAction, default=None, help="Include online episode title in TV filename")
    parser.add_argument("--json-summary", action="store_true", help="Print machine-readable JSON summary")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error logs")
    return parser


def apply_cli_overrides(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    cfg = dict(config)
    online_cfg = dict(cfg.get("online_lookup", {}))

    if args.dry_run is not None:
        cfg["dry_run"] = bool(args.dry_run)
    if args.movies is not None:
        cfg["organize_movies"] = bool(args.movies)
    if args.tv is not None:
        cfg["organize_tv"] = bool(args.tv)
    if args.online_lookup is not None:
        online_cfg["enabled"] = bool(args.online_lookup)
    if args.include_episode_title is not None:
        online_cfg["include_episode_title"] = bool(args.include_episode_title)

    cfg["online_lookup"] = online_cfg
    return cfg


def write_starter_config(path: str) -> Path:
    config_path = Path(path).expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(default_config(), indent=2), encoding="utf-8")
    return config_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.init_config:
        path = write_starter_config(args.init_config)
        print(f"Wrote starter config: {path}")
        return 0

    base_path = Path(args.path).expanduser().resolve()
    if not base_path.exists() or not base_path.is_dir():
        print(f"Error: base path does not exist or is not a directory: {base_path}", file=sys.stderr)
        return 2

    try:
        config = deep_merge(default_config(), load_json_config(args.config))
        config = apply_cli_overrides(config, args)
    except Exception as exc:
        print(f"Error loading configuration: {exc}", file=sys.stderr)
        return 2

    organizer = Organizer(base_path=base_path, config=config, verbose=not args.quiet)
    summary = organizer.run()

    if args.json_summary:
        print(json.dumps(summary.to_dict(), indent=2))
    else:
        print("=" * 60)
        print("Media Organizer Summary")
        print("=" * 60)
        print(f"Base path: {summary.base_path}")
        print(f"Dry run: {summary.dry_run}")
        print(f"Scanned: {summary.scanned}")
        print(f"Processed: {summary.processed}")
        print(f"Skipped: {summary.skipped}")
        print(f"Failed: {summary.failed}")
        print(f"Movie folders processed: {summary.movies_processed}")
        print(f"TV files renamed: {summary.tv_files_renamed}")

    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
