from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from local_call_agent.domain import SessionPaths, TranscriptSegment


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:48] or "call"


def create_session_paths(root: Path, label: str, started_at: datetime) -> SessionPaths:
    base_stem = f"{started_at:%Y-%m-%d}-{safe_name(label)}-{started_at:%H%M%S}"
    for sequence in range(1, 1000):
        stem = base_stem if sequence == 1 else f"{base_stem}-{sequence}"
        directory = root / stem
        try:
            directory.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError("could not allocate a unique session directory")
    transcript = directory / f"{stem}-transcript.md"
    return SessionPaths(directory, transcript, directory / f"{stem}-segments.jsonl",
                        directory / f"{stem}-transcript-summary.md")


class RollingTranscriptWriter:
    def __init__(self, paths: SessionPaths, started_at: datetime) -> None:
        self.paths = paths
        self._started_at = started_at
        self._segments: list[TranscriptSegment] = []
        self._render()

    def append(self, segments: list[TranscriptSegment]) -> None:
        if not segments:
            return
        with self.paths.segments.open("a", encoding="utf-8") as output:
            for segment in segments:
                output.write(json.dumps({"started_at": segment.started_at.isoformat(),
                                         "ended_at": segment.ended_at.isoformat(),
                                         "text": segment.text, "source": segment.source}) + "\n")
        self._segments.extend(segments)
        self._segments.sort(key=lambda item: item.started_at)
        self._render()

    def _render(self) -> None:
        lines = ["# Live transcript", "", f"Started: {self._started_at.isoformat()}", ""]
        lines.extend(f"- **{s.started_at:%H:%M:%S}** {s.text}" for s in self._segments)
        temporary = self.paths.transcript.with_suffix(".tmp")
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        os.replace(temporary, self.paths.transcript)

    @property
    def text(self) -> str:
        return "\n".join(segment.text for segment in self._segments)
