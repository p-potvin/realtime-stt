# 🎙️ Real-Time STT (Speech-to-Text)

A premium, privacy-first real-time transcription tool under the **VaultWares** umbrella. Designed for low-latency live captions, this application captures audio natively from Windows default speakers and displays a sleek, click-through overlay on top of your workspace.

## 🚀 Features

- **Live Transcription:** Real-time audio-to-text using `NVIDIA Parakeet` as default, or `Faster-Whisper` for fast standard transcriptions.
- **Out-of-the-Box System Loopback:** Captures native Windows speaker output seamlessly without needing extra virtual cables.
- **Unobtrusive Overlay & System Tray:** A completely click-through, scalable caption window controlled cleanly via a system tray utility.
- **Persistent Configuration:** Remembers your font choices, text styling, model selections, and themes via an auto-generating `config.json` file.
- **Hardware Accelerated:** Full CUDA support for RTX 30-series GPUs (Optimized for RTX 3060 12GB).
- **Intelligent VAD:** Integrated Silero VAD to isolate speech and ignore background noise/music.
- **VaultWares Themes:** Supports both Solarized Dark and Light modes with Segoe UI typography.

## 🛠️ Tech Stack

- **Engine:** Python 3.10+
- **STT:** NVIDIA Parakeet (Primary) / Faster-Whisper (Secondary)
- **VAD:** Silero VAD
- **GUI:** PySide6 (Qt for Python)
- **Audio:** `soundcard` library for native WASAPI Desktop Speaker Loopback

## 📋 Requirements

- NVIDIA GPU with 8GB+ VRAM (RTX 3060 12GB recommended).
- [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) installed.

## ⚙️ Installation

1. Create a local virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. install dependencies:
```powershell
pip install -r requirements.txt
```

  # 🏃 Running the App
Following VaultWares standards, use the provided .cmd wrapper:
```powershell
realtime-stt
```

# 🗺️ Roadmap
See ROADMAP.md for the full feature path and upcoming optimizations.

# 🔒 Privacy & Security
As with all VaultWares projects, your data stays local. Transcription is performed entirely on your device using your GPU. No audio data or text is ever sent to external servers.

--------------------------------------------
*© 2026 VaultWares. All rights reserved.*