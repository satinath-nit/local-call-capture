from __future__ import annotations

from contextlib import ExitStack
from datetime import datetime, timezone
from queue import Full, Queue
from typing import Iterable

import numpy as np
import sounddevice as sd

from local_call_agent.config import AudioConfig
from local_call_agent.domain import AudioBlock


def list_input_devices() -> Iterable[dict]:
    for index, device in enumerate(sd.query_devices()):
        if device["max_input_channels"] > 0:
            yield {"index": index, "name": device["name"], "channels": device["max_input_channels"]}


class AudioCapture:
    """Owns callback streams and safely hands mono blocks to a worker queue."""

    def __init__(self, config: AudioConfig, output: Queue[AudioBlock]) -> None:
        self._config = config
        self._output = output
        self.dropped_blocks = 0
        self._stack: ExitStack | None = None

    def _callback(self, source: str):
        def push(indata: np.ndarray, frames: int, time_info: object, status: sd.CallbackFlags) -> None:
            if status:
                print(f"audio {source} status: {status}")
            mono = np.asarray(indata[:, 0], dtype=np.float32).copy()
            try:
                self._output.put_nowait(AudioBlock(mono, datetime.now(timezone.utc), source))
            except Full:
                self.dropped_blocks += 1
        return push

    def start(self) -> None:
        devices = [("microphone", self._config.microphone_device)]
        if self._config.system_audio_device:
            devices.append(("system", self._config.system_audio_device))
        if not any(device for _, device in devices):
            raise ValueError("set audio.microphone_device or audio.system_audio_device in config.yaml")

        self._stack = ExitStack()
        blocksize = self._config.sample_rate * self._config.block_duration_ms // 1000
        for source, device in devices:
            if device is None:
                continue
            stream = sd.InputStream(
                device=device,
                channels=1,
                samplerate=self._config.sample_rate,
                blocksize=blocksize,
                dtype="float32",
                callback=self._callback(source),
            )
            self._stack.enter_context(stream)

    def stop(self) -> None:
        if self._stack:
            self._stack.close()
            self._stack = None
