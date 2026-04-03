# 🗺️ Project Roadmap: Real-Time STT

This roadmap outlines the development phases and goals for the Real-Time Speech-to-Text project, adhering to **VaultWares** performance and design standards.

## 🎯 Project Goals
- Achieve sub-500ms latency from speech to caption display.
- Maintain a minimalist, non-intrusive transparent overlay.
- Optimize VRAM usage to allow simultaneous gaming or heavy workloads on an RTX 3060.
- Provide a robust, privacy-first alternative to cloud-based STT services.

---

## 📅 Roadmap Phases

### Phase 1: Foundation & Reusability (Completed)
- [x] Define project scope and roadmap.
- [x] Create VaultWares-compliant documentation.
- [x] Import and adapt `Faster-Whisper` wrapper from `video-transcriber-translator`.
- [x] Integrate `NVIDIA Parakeet` as primary STT.
- [x] Set up the basic Python environment and project structure.

### Phase 2: Audio Engineering & VAD (Completed)
- [x] Implement audio capture using `soundcard` with native WASAPI loopback support.
- [x] Integrate **Silero VAD** for efficient speech activity detection.
- [x] Develop a chunk-based buffering system to manage audio streams.
- [ ] Research and implement optional **Demucs** vocal isolation if compute headroom permits.

### Phase 3: The Glass UI (PySide6) (Completed)
- [x] Design a frameless, "always-on-top" caption window with floating Dropshadow text.
- [x] Implement click-through transparency (OS-level integration).
- [x] Embed **Segoe UI** typography styling and text alignment choices.
- [x] Add support for VaultWares theme modules.

### Phase 4: Integration & Synchronization (Current)
- [x] Bridge the STT engine output to the PySide6 UI thread via QSignals.
- [x] Add persistent configuration (`config.json` for font size, typography, audio model engine).
- [x] Move configuration dashboard to a System Tray utility.
- [ ] Implement smooth text scrolling and "fading out" of old captions.

### Phase 5: Optimization & Cleanup
- [x] Implement **CorrelationId** logging for enterprise-level debugging.
- [x] Create distribution scripts (`realtime-stt.cmd`).
- [ ] Optimize GPU compute schedules to minimize impact on other CUDA-accelerated apps.

---

## 📈 Future Possibilities
- Multi-language live translation (STT + Translation pipeline).
- Custom dictionary support for niche terminology or jargon.
- Voice-activated UI controls for transcription management.

---
*Last Updated: 2026-03-26*
