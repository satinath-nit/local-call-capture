from local_call_agent.config import OllamaConfig
from local_call_agent.llm.ollama import OllamaSummarizer


def test_summarizer_retries_false_empty_response(monkeypatch) -> None:
    responses = iter(["No content was transcribed.\n", "# Call summary\n\n## Summary\nWe chose a plan.\n"])
    summarizer = OllamaSummarizer(OllamaConfig())
    monkeypatch.setattr(summarizer, "_generate", lambda prompt: next(responses))

    assert "We chose a plan" in summarizer.summarize("We chose a plan.")


def test_summarizer_empty_transcript_does_not_contact_ollama(monkeypatch) -> None:
    summarizer = OllamaSummarizer(OllamaConfig())
    monkeypatch.setattr(summarizer, "_generate", lambda prompt: (_ for _ in ()).throw(AssertionError()))

    assert "No content was transcribed" in summarizer.summarize("")
