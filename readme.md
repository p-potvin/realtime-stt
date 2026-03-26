# 🎙️ Real-Time STT (Speech-to-Text)

A premium, privacy-first real-time transcription tool under the **VaultWares** umbrella. Designed for low-latency live captions, this application captures audio from virtual cables (like VoiceMeeter) and displays a sleek, transparent overlay on top of your workspace.

## 🚀 Features

- **Live Transcription:** Real-time audio-to-text using `Faster-Whisper` (leveraging CTranslate2 for maximum speed).
- **Virtual Cable Support:** Optimized for VoiceMeeter / VB-Audio virtual output cables.
- **Glass UI Overlay:** A minimalist, "always-on-top" caption window built with PySide6.
- **Hardware Accelerated:** Full CUDA support for RTX 30-series GPUs (Optimized for RTX 3060 12GB).
- **Intelligent VAD:** Integrated Silero VAD to isolate speech and ignore background noise/music.
- **VaultWares Themes:** Supports both Solarized Dark and Light modes with Segoe UI Semilight typography.

## 🛠️ Tech Stack

- **Engine:** Python 3.10+
- **STT:** Faster-Whisper (imported and adapted from `video-transcriber-translator`)
- **VAD:** Silero VAD
- **GUI:** PySide6 (Qt for Python)
- **Audio:** `sounddevice` / WASAPI Loopback

## 📋 Requirements

- NVIDIA GPU with 8GB+ VRAM (RTX 3060 12GB recommended).
- [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) installed.
- [VoiceMeeter](https://vb-audio.com/Voicemeeter/) or VB-Cable for audio routing.

## ⚙️ Installation

1. Create a local virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate

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