from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from local_call_agent.config import VadConfig


@dataclass
class SpeechChunker:
    """Energy-based VAD that yields complete speech chunks without blocking capture."""

    config: VadConfig
    sample_rate: int
    _speech_ms: int = 0
    _silence_ms: int = 0
    _active: bool = False
    _buffers: list[np.ndarray] | None = None

    def __post_init__(self) -> None:
        self._buffers = []

    def push(self, samples: np.ndarray) -> np.ndarray | None:
        duration_ms = round(len(samples) / self.sample_rate * 1000)
        energy = float(np.sqrt(np.mean(np.square(samples)))) if len(samples) else 0.0
        speaking = energy >= self.config.energy_threshold

        if speaking:
            self._speech_ms += duration_ms
            self._silence_ms = 0
        else:
            self._silence_ms += duration_ms

        if not self._active and self._speech_ms >= self.config.speech_start_ms:
            self._active = True
        if self._active:
            self._buffers.append(samples)
            total_ms = sum(len(item) for item in self._buffers) / self.sample_rate * 1000
            if self._silence_ms >= self.config.silence_end_ms or total_ms >= self.config.max_chunk_ms:
                return self.flush()
        elif not speaking:
            self._speech_ms = 0
        return None

    def flush(self) -> np.ndarray | None:
        if not self._buffers:
            return None
        samples = np.concatenate(self._buffers)
        self._buffers = []
        self._active = False
        self._speech_ms = 0
        self._silence_ms = 0
        min_samples = self.sample_rate * self.config.min_chunk_ms // 1000
        return samples if len(samples) >= min_samples else None
