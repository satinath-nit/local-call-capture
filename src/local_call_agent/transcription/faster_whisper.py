from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from local_call_agent.config import TranscriptionConfig
from local_call_agent.domain import TranscriptSegment


class FasterWhisperTranscriber:
    def __init__(self, config: TranscriptionConfig) -> None:
        from faster_whisper import WhisperModel

        device = "cpu"
        compute_type = config.cpu_compute_type
        try:
            import ctranslate2
            if ctranslate2.get_supported_compute_types("cuda"):
                device, compute_type = "cuda", config.cuda_compute_type
        except Exception:
            pass
        self._model = WhisperModel(config.model, device=device, compute_type=compute_type,
                                  local_files_only=True)
        self._language = config.language

    def transcribe(self, audio: np.ndarray, captured_at: datetime) -> list[TranscriptSegment]:
        segments, _ = self._model.transcribe(audio, language=self._language, vad_filter=False)
        result: list[TranscriptSegment] = []
        for segment in segments:
            text = segment.text.strip()
            if text:
                result.append(TranscriptSegment(
                    started_at=captured_at + timedelta(seconds=segment.start),
                    ended_at=captured_at + timedelta(seconds=segment.end),
                    text=text,
                ))
        return result
