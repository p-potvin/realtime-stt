<img src="https://raw.githubusercontent.com/p-potvin/vault-themes/refs/heads/main/assets/logos/vaultwares-logo-dark.svg">
# realtime-stt

**Real-Time Speech-to-Text Engine**  
**Part of the VaultWares Ecosystem** • <a href="https://docs.vaultwares.com">docs.vaultwares.com</a> • <a href="https://vaultwares.com">vaultwares.com</a>

**High-performance, local-first real-time STT service (faster-whisper / Whisper-based) with low-latency streaming, multi-language support, and seamless integration into vaultwares-pipelines and vault-flows.**

## Overview
This component provides real-time transcription and translation capabilities for video, audio streams, live meetings, and media processing pipelines across the VaultWares ecosystem.

## Features
- Real-time streaming transcription
- Multi-language support + auto-translation
- Local-first execution (GPU/CPU optimized)
- Fault-Tolerant Hardware Management (Automatic CPU fallback for models)
- WebSocket / HTTP streaming endpoints
- Integration with vaultwares-pipelines for end-to-end media workflows
- Low-latency mode for vault-player and vault-flows
- Multi-segment handling optimization (Near real-time algorithms, VAD slicing)
- Audio Volume Normalization (Dynamic peak AGC)
- Agent-aware monitoring hooks
- Persistent JSON configuration (`config.json`)
- Glass UI 9-theme system
- WASAPI loopback support out-of-the-box (via `soundcard`)

## Quick Start

```bash
git clone https://github.com/p-potvin/realtime-stt.git
cd realtime-stt
git submodule update --init --recursive
pip install -r requirements.txt
python run_server.py
```

Architecture &amp; Agent Integration
Fully synchronized with the VaultWares Agent Knowledge Dissemination System:
→ https://raw.githubusercontent.com/p-potvin/vaultwares-docs/main/agents/knowledge-dissemination.mdx
Can invoke the full coordinated agent team via invoke_vaultwares_team skill from vaultwares-agentciation.
Privacy &amp; Security

All processing happens locally by default
No cloud transcription unless explicitly configured
Encrypted WebSocket option
Full threat model in central VaultWares docs

Contributing
See CONTRIBUTING.md and the central Brand Guidelines.
License
GPL-3.0 (see LICENSE)
Built with ❤️ for privacy
