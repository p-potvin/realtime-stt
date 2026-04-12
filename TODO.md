# Real-Time STT Dashboard

- [x] Initial Scaffolding & Documentation.
- [x] GPU/CUDA STT Integration (Faster-Whisper on RTX 3060).
- [x] Audio Capture & VAD filtering (Silero).
- [x] Fault-Tolerant Hardware Management (Automatic CPU fallback for models).
- [x] GUI Overlay with Subtitle custom styling & Outlining.
- [x] VaultWares Theme Management (9 specific color combinations).
- [x] Dynamic Debugging Controls (Global Log Level Toggle).
- [x] CLI & GUI Target Language support (default: 'en').
- [x] Integrate NVIDIA Parakeet STT as default engine.
- [x] Configure JSON system settings persistence (`config.json`).
- [x] Background Tray Icon & decoupled transparent overlay.
- [x] WASAPI loopback support out-of-the-box (via `soundcard`).
- [x] Multi-segment handling optimization (Near real-time algorithms, VAD slicing).
- [x] Audio Volume Normalization (Fix ~0.25 peaking from 2.5x gain threshold, use dynamic peak AGC).
