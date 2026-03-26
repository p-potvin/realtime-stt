# 🗺️ Project Roadmap: Real-Time STT

This roadmap outlines the development phases and goals for the Real-Time Speech-to-Text project, adhering to **VaultWares** performance and design standards.

## 🎯 Project Goals
- Achieve sub-500ms latency from speech to caption display.
- Maintain a minimalist, non-intrusive transparent overlay.
- Optimize VRAM usage to allow simultaneous gaming or heavy workloads on an RTX 3060.
- Provide a robust, privacy-first alternative to cloud-based STT services.

---

## 📅 Roadmap Phases

### Phase 1: Foundation & Reusability (Current)
- [x] Define project scope and roadmap.
- [x] Create VaultWares-compliant documentation.
- [ ] Import and adapt `Faster-Whisper` wrapper from `video-transcriber-translator`.
- [ ] Set up the basic Python environment and project structure.

### Phase 2: Audio Engineering & VAD
- [ ] Implement audio capture using `sounddevice` with WASAPI loopback support.
- [ ] Integrate **Silero VAD** for efficient speech activity detection.
- [ ] Develop a chunk-based buffering system to manage audio streams for `Faster-Whisper`.
- [ ] Research and implement optional **Demucs** vocal isolation if compute headroom permits.

### Phase 3: The Glass UI (PySide6)
- [ ] Design a frameless, "always-on-top" caption window.
- [ ] Implement click-through transparency (OS-level integration).
- [ ] Embed **Segoe UI Semilight** typography and gradient-accented themes.
- [ ] Add support for "Dark" (Solarized base) and "Light" UI skins.

### Phase 4: Integration & Synchronization
- [ ] Bridge the STT engine output to the PySide6 UI thread.
- [ ] Implement smooth text scrolling and "fading out" of old captions.
- [ ] Add basic configuration (font size, opacity, audio device selection).

### Phase 5: Optimization & Cleanup
- [ ] Implement **CorrelationId** logging for enterprise-level debugging.
- [ ] Optimize GPU compute schedules to minimize impact on other CUDA-accelerated apps.
- [ ] Create distribution scripts (`realtime-stt.cmd`).

---

## 📈 Future Possibilities
- Multi-language live translation (STT + Translation pipeline).
- Custom dictionary support for niche terminology or jargon.
- Voice-activated UI controls for transcription management.

---
*Last Updated: 2026-03-26*
