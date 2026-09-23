# Local Call Capture

`local-call-agent` is a macOS command-line app for privately transcribing calls. It captures your microphone plus a local system-audio loopback, writes a live Markdown transcript with `faster-whisper`, and creates Markdown meeting notes with a local Ollama model.

It works with Teams, Zoom, Tuple, Slack Huddles, and browser calls because it transcribes the audio routed through your Mac—not an app-specific recording feature.

## Privacy and consent

Use this only when all required participants have been informed and you have authorization under applicable law, company policy, and platform rules.

After the one-time installation and model downloads, the app can run offline. It uses no cloud transcription or LLM API. Ollama is restricted to your machine's loopback address, and Whisper is configured not to download models during a call.

## Requirements

- macOS
- Python 3.11+ (`python3 --version`)
- An internet connection for one-time setup
- [Ollama for macOS](https://ollama.com/download)
- [BlackHole 2ch](https://existential.audio/blackhole/) for system-audio routing
- About 8 GB of free disk space and enough memory for the selected Ollama model

Use your installed Python first, including Python 3.14. If a native dependency has no compatible wheel, use Python 3.12 only for this project's virtual environment—it does not replace your system Python.

## 1. Install the project

Clone or copy this repository to a local folder, then create an isolated Python environment:

```bash
cd /path/to/local-call-capture

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e '.[dev]'
```

Every new terminal session requires:

```bash
cd /path/to/local-call-capture
source .venv/bin/activate
```

## 2. Download the local models once

With the virtual environment active, download the Whisper transcription model into this project:

```bash
mkdir -p models
hf download Systran/faster-whisper-small.en \
  --local-dir models/faster-whisper-small.en
```

If your installation provides the older command instead, use:

```bash
huggingface-cli download Systran/faster-whisper-small.en \
  --local-dir models/faster-whisper-small.en
```

`small.en` is an English model of roughly 486 MB and is a good CPU-quality starting point. The sample configuration points to this local folder.

Install [Ollama](https://ollama.com/download), open it once, then download the local summary model:

```bash
ollama --version
ollama pull qwen2.5:7b
ollama list
```

Ollama manages its own downloaded models under `/Users/<your-user>/.ollama/models`; do not move those files manually.

## 3. Route Mac audio through BlackHole

Install BlackHole's two-channel driver:

```bash
brew install blackhole-2ch
```

If `BlackHole 2ch` is not visible in **Audio MIDI Setup**, quit that app and restart the Mac.

Configure routing:

1. Open **Audio MIDI Setup** (`⌘ Space`, then type its name).
2. Click **+** in the lower-left corner → **Create Multi-Output Device**.
3. Enable both your real speakers/headphones and **BlackHole 2ch**.
4. Keep the real speakers/headphones as the **Primary Device**.
5. Enable **Drift Correction** for BlackHole, not for the primary device.
6. Open **System Settings → Sound → Output** and select the new **Multi-Output Device**.

This sends call audio to your ears and BlackHole at the same time. Do not select BlackHole by itself as the Mac output device, or you will not hear the call.

For Bluetooth or USB headphones, use them—not MacBook speakers—as the Multi-Output Device's primary device.

## 4. Configure the agent

List input devices:

```bash
local-call-agent devices
```

Create your machine-local configuration:

```bash
cp config.example.yaml config.yaml
```

Use the names printed above exactly. A typical MacBook configuration is:

```yaml
audio:
  microphone_device: "MacBook Pro Microphone"
  system_audio_device: "BlackHole 2ch"
  sample_rate: 16000
```

`config.yaml` is Git-ignored and stays only on that machine. Change `output.session_label` to identify sessions, for example `planning-call`.

## 5. Record and summarize

Start capture:

```bash
local-call-agent run --config config.yaml
```

On first use, allow your terminal application in **System Settings → Privacy & Security → Microphone**. Confirmed transcript lines appear after a brief silence.

Press `Ctrl-C` to finish. The app finalizes the transcript and writes a local Ollama summary.

Each session has its own unique folder, so no call is overwritten:

```text
recordings/2026-09-23-call-214500/
├── 2026-09-23-call-214500-transcript.md
├── 2026-09-23-call-214500-segments.jsonl
└── 2026-09-23-call-214500-transcript-summary.md
```

- `transcript.md`: readable rolling transcript
- `segments.jsonl`: timestamped structured transcript data
- `transcript-summary.md`: local meeting notes

To regenerate a summary without recording again:

```bash
local-call-agent summarize \
  recordings/2026-09-23-call-214500/2026-09-23-call-214500-transcript.md \
  --config config.yaml
```

## Configuration reference

| Setting | Purpose |
| --- | --- |
| `vad.energy_threshold` | Raise it when noise triggers transcription; lower it if quiet speech is missed. |
| `vad.silence_end_ms` | Silence duration that ends a speech chunk; lower values show text sooner. |
| `transcription.model` | Local directory containing the CTranslate2 Whisper model. |
| `transcription.cpu_compute_type` | `int8` is the efficient CPU default. |
| `ollama.model` | A model already pulled into local Ollama. |
| `output.directory` | Destination folder for transcripts and summaries. |

## Troubleshooting

### The app hears you but not other call participants

- Confirm **Multi-Output Device** is selected in macOS Sound Output.
- Confirm both your speakers/headphones and BlackHole are enabled in that device.
- Run `local-call-agent devices`; `BlackHole 2ch` must appear.
- Confirm `system_audio_device: "BlackHole 2ch"` in `config.yaml`.

### Nothing is transcribed

- Grant microphone access to the terminal application.
- Verify that device names exactly match `local-call-agent devices` output.
- Speak louder or lower `vad.energy_threshold`, for example to `0.008`.
- Confirm `models/faster-whisper-small.en/model.bin` exists.

### Ollama summary fails

- Open Ollama and run `ollama list`.
- Confirm `qwen2.5:7b` appears; otherwise run `ollama pull qwen2.5:7b`.
- Keep `ollama.url` as `http://127.0.0.1:11434`; remote endpoints are intentionally rejected.

### Closing Terminal stops recording

This is a command-line application: the terminal process owns the active capture session. Closing it safely stops recording. A future menu-bar app or LaunchAgent can make it run in the background.

## Development checks

```bash
source .venv/bin/activate
pytest -q
```

The unit tests do not require a microphone, Whisper model, or running Ollama server.
