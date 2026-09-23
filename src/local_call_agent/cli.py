from __future__ import annotations

import argparse
from pathlib import Path

from local_call_agent.app import CallAgent
from local_call_agent.audio.capture import list_input_devices
from local_call_agent.config import load_config
from local_call_agent.llm.ollama import OllamaSummarizer


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline microphone and local-loopback transcriber")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("devices", help="list usable input device names")
    run = commands.add_parser("run", help="start a local transcription session")
    run.add_argument("--config", type=Path, default=Path("config.yaml"))
    summarize = commands.add_parser("summarize", help="regenerate a local summary from a transcript")
    summarize.add_argument("transcript", type=Path)
    summarize.add_argument("--config", type=Path, default=Path("config.yaml"))
    args = parser.parse_args()

    if args.command == "devices":
        for device in list_input_devices():
            print(f'[{device["index"]}] {device["name"]} ({device["channels"]} input channels)')
        return
    if args.command == "summarize":
        transcript = args.transcript
        if not transcript.is_file():
            parser.error(f"transcript not found: {transcript}")
        summary = transcript.with_name(f"{transcript.stem}-summary.md")
        OllamaSummarizer(load_config(args.config).ollama).write_summary(summary, transcript.read_text())
        print(f"Summary written to {summary}")
        return
    CallAgent(load_config(args.config)).run()


if __name__ == "__main__":
    main()
