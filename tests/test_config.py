from pathlib import Path

import pytest

from local_call_agent.config import load_config


def test_config_rejects_remote_ollama(tmp_path: Path) -> None:
    config = tmp_path / "config.yaml"
    config.write_text("ollama:\n  url: https://example.com\n")
    with pytest.raises(ValueError, match="loopback"):
        load_config(config)
