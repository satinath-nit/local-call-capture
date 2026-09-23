import numpy as np

from local_call_agent.audio.vad import SpeechChunker
from local_call_agent.config import VadConfig


def test_chunker_emits_after_silence() -> None:
    chunker = SpeechChunker(VadConfig(energy_threshold=0.1, speech_start_ms=100,
                                      silence_end_ms=200, min_chunk_ms=100, max_chunk_ms=1000), 1000)
    assert chunker.push(np.ones(100, dtype=np.float32)) is None
    assert chunker.push(np.zeros(100, dtype=np.float32)) is None
    result = chunker.push(np.zeros(100, dtype=np.float32))
    assert result is not None
    assert len(result) == 300
