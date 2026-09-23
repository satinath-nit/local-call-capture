from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import yaml


@dataclass(frozen=True)
class AudioConfig:
    microphone_device: str | int | None = None
    system_audio_device: str | int | None = None
    sample_rate: int = 16000
    block_duration_ms: int = 100
    queue_max_blocks: int = 300


@dataclass(frozen=True)
class VadConfig:
    energy_threshold: float = 0.012
    speech_start_ms: int = 300
    silence_end_ms: int = 900
    min_chunk_ms: int = 700
    max_chunk_ms: int = 30000


@dataclass(frozen=True)
class TranscriptionConfig:
    model: str = "small.en"
    language: str | None = "en"
    cpu_compute_type: str = "int8"
    cuda_compute_type: str = "float16"


@dataclass(frozen=True)
class OllamaConfig:
    url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:7b"
    timeout_seconds: int = 180


@dataclass(frozen=True)
class OutputConfig:
    directory: Path = Path("recordings")
    session_label: str = "call"


@dataclass(frozen=True)
class AppConfig:
    audio: AudioConfig
    vad: VadConfig
    transcription: TranscriptionConfig
    ollama: OllamaConfig
    output: OutputConfig


def _section(data: dict, name: str) -> dict:
    value = data.get(name, {})
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a mapping")
    return value


def load_config(path: Path) -> AppConfig:
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError("configuration root must be a mapping")
    output = _section(data, "output")
    config = AppConfig(
        audio=AudioConfig(**_section(data, "audio")),
        vad=VadConfig(**_section(data, "vad")),
        transcription=TranscriptionConfig(**_section(data, "transcription")),
        ollama=OllamaConfig(**_section(data, "ollama")),
        output=OutputConfig(directory=Path(output.get("directory", "recordings")),
                            session_label=output.get("session_label", "call")),
    )
    validate_config(config)
    return config


def validate_config(config: AppConfig) -> None:
    if config.audio.sample_rate <= 0 or config.audio.block_duration_ms <= 0:
        raise ValueError("audio sample_rate and block_duration_ms must be positive")
    if config.vad.energy_threshold < 0:
        raise ValueError("vad.energy_threshold must be non-negative")
    if config.vad.max_chunk_ms < config.vad.min_chunk_ms:
        raise ValueError("vad.max_chunk_ms must be at least vad.min_chunk_ms")
    host = urlparse(config.ollama.url).hostname
    if host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("ollama.url must point to a local loopback host")
