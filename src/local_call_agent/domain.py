from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class AudioBlock:
    samples: np.ndarray
    captured_at: datetime
    source: str


@dataclass(frozen=True)
class TranscriptSegment:
    started_at: datetime
    ended_at: datetime
    text: str
    source: str = "mixed"


@dataclass(frozen=True)
class SessionPaths:
    directory: Path
    transcript: Path
    segments: Path
    summary: Path
