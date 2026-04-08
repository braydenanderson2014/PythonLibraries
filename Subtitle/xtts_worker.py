#!/usr/bin/env python3
"""Dedicated XTTS worker process.

Runs one synthesis request per invocation so the main GUI process can keep
Whisper/ASR dependencies separate from Coqui XTTS dependencies.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="XTTS worker")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--speaker-wav", required=True, help="Reference speaker wav path")
    parser.add_argument("--language", required=True, help="XTTS language code")
    parser.add_argument("--output", required=True, help="Output wav path")
    parser.add_argument(
        "--model",
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        help="Coqui model name",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    # PyTorch 2.6+ changed torch.load default to weights_only=True, which can
    # break trusted XTTS checkpoints that rely on config class unpickling.
    # This worker loads only Coqui model assets and is used for local tooling.
    os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
    # Prefer legacy torchaudio backend dispatch when available; newer dispatcher
    # may require torchcodec in some environments.
    os.environ.setdefault("TORCHAUDIO_USE_BACKEND_DISPATCHER", "0")

    from TTS.api import TTS  # Imported here so import errors are reported by worker.

    text = (args.text or "").strip()
    if not text:
        raise ValueError("text is empty")

    speaker_wav = Path(args.speaker_wav)
    if not speaker_wav.exists():
        raise FileNotFoundError(f"speaker wav not found: {speaker_wav}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        tts = TTS(args.model)
    except Exception as exc:
        message = str(exc)
        if "TorchCodec is required" in message or "torchcodec" in message.lower():
            raise RuntimeError(
                "XTTS model load failed because torchaudio requested TorchCodec. "
                "Install torchcodec in venv_xtts, or use a torchaudio build/backend that does not require it. "
                f"Original error: {message}"
            ) from exc
        if "Weights only load failed" in message or "WeightsUnpickler" in message:
            raise RuntimeError(
                "XTTS model load failed due to PyTorch weights_only checkpoint policy. "
                "Use torch<2.6 in venv_xtts or ensure TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1 is set. "
                f"Original error: {message}"
            ) from exc
        raise
    tts.tts_to_file(
        text=text,
        speaker_wav=str(speaker_wav),
        language=str(args.language or "en"),
        file_path=str(output_path),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
