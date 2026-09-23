from __future__ import annotations

import queue
import threading
from datetime import datetime, timezone

import numpy as np

from local_call_agent.audio.capture import AudioCapture
from local_call_agent.audio.vad import SpeechChunker
from local_call_agent.config import AppConfig
from local_call_agent.domain import AudioBlock
from local_call_agent.llm.ollama import OllamaSummarizer
from local_call_agent.transcript.writer import RollingTranscriptWriter, create_session_paths
from local_call_agent.transcription.faster_whisper import FasterWhisperTranscriber


class CallAgent:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._blocks: queue.Queue[AudioBlock] = queue.Queue(maxsize=config.audio.queue_max_blocks)
        self._stop = threading.Event()

    def run(self) -> None:
        started_at = datetime.now(timezone.utc)
        paths = create_session_paths(self.config.output.directory, self.config.output.session_label, started_at)
        writer = RollingTranscriptWriter(paths, started_at)
        capture = AudioCapture(self.config.audio, self._blocks)
        transcriber = FasterWhisperTranscriber(self.config.transcription)
        chunkers: dict[str, SpeechChunker] = {}

        print("RECORDING/TRANSCRIPTION ACTIVE — ensure all required participants have been notified.")
        print(f"Writing transcript to {paths.transcript}")
        capture.start()
        try:
            while not self._stop.is_set():
                try:
                    block = self._blocks.get(timeout=0.5)
                except queue.Empty:
                    continue
                chunker = chunkers.setdefault(
                    block.source, SpeechChunker(self.config.vad, self.config.audio.sample_rate)
                )
                speech = chunker.push(block.samples)
                if speech is not None:
                    self._write_segments(transcriber, writer, speech, block.captured_at)
        except KeyboardInterrupt:
            print("Finalizing session...")
        finally:
            capture.stop()
            for chunker in chunkers.values():
                remainder = chunker.flush()
                if remainder is not None:
                    self._write_segments(transcriber, writer, remainder, datetime.now(timezone.utc))
            if capture.dropped_blocks:
                print(f"Warning: dropped {capture.dropped_blocks} audio blocks because processing fell behind.")
            OllamaSummarizer(self.config.ollama).write_summary(paths.summary, writer.text)
            print(f"Summary written to {paths.summary}")

    @staticmethod
    def _write_segments(transcriber: FasterWhisperTranscriber, writer: RollingTranscriptWriter,
                        speech: np.ndarray, captured_at: datetime) -> None:
        segments = transcriber.transcribe(speech, captured_at)
        writer.append(segments)
        for segment in segments:
            print(f"[{segment.started_at:%H:%M:%S}] {segment.text}")
