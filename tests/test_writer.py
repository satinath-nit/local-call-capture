from datetime import datetime, timezone

from local_call_agent.domain import TranscriptSegment
from local_call_agent.transcript.writer import RollingTranscriptWriter, create_session_paths


def test_writer_persists_markdown_and_jsonl(tmp_path) -> None:
    now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    paths = create_session_paths(tmp_path, "Planning Call", now)
    writer = RollingTranscriptWriter(paths, now)
    writer.append([TranscriptSegment(now, now, "Decide on the routing.")])
    assert "Decide on the routing." in paths.transcript.read_text()
    assert '"text": "Decide on the routing."' in paths.segments.read_text()


def test_sessions_started_at_same_second_do_not_overwrite_each_other(tmp_path) -> None:
    now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    first = create_session_paths(tmp_path, "Call", now)
    second = create_session_paths(tmp_path, "Call", now)

    assert first.directory != second.directory
    assert second.directory.name.endswith("-2")
