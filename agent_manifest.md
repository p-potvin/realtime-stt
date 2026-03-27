# 📑 Project Manifest (Elephant Coder)

    Updated: 2026-03-27

# 🎯 Current Mission Control

    Active Goal: [x] Core Infrastructure & Template Injection [ ] Real-time Engine & Model Optimization.

    Success Criteria: 
    - Real-time transcription using Faster-Whisper (target RTX 3060).
    - Intelligent speech detection using Silero VAD (512-sample blocksize).
    - Draggable, resizable, transparent PySide6 overlay with "Glass UI" 9-theme system.
    - Advanced customization: Color pickers for text/outline, SpinBoxes for size/width, double-click to reset position.

    Update Policy: Omit "Summary of Accomplishments" in tasks unless requested.

# 📜 Coding Standards & Refactoring Logic
    **CRITICAL**: Always perform a complete code cleanup after refactoring.
    - **No Dead Code**: Remove all unused imports, variables, and orphan functions immediately.
    - **Scan for Drift**: Before finishing, verify that indentations, scoping, and logic remain clean.
    - **Instruction Persistence**: All future changes must follow the guidelines in `INSTRUCTIONS.md`.

# 🏗️ Architectural Map (The "Memory Bank")

    Core Patterns: 
    - Functional/Modular Python for STT engine.
    - Signal/Slot pattern (PySide6) for engine-to-GUI communication.
    - Glass UI & 9-Theme System (VaultWares Standards).
    - Hardware Fallback: CUDA (default) to CPU (fallback) for Whisper models.

    Global Singletons/Contexts: 
    - `TransparentOverlay`: The main UI orchestrator.
    - `VaultThemeManager`: Centralized theme library (Submodule: `vault_themes/`).
    - `VaultSyncManager`: Handles Git Submodule synchronization via `VAULT_DEPENDENCIES.txt`.
    - `FasterWhisperWrapper`: Handles model inference.
    - `VADLogic`: Handles voice activity detection.

    Standard Error Handling: 
    - Internal Package Manager: `vault_sync.py` reads `VAULT_DEPENDENCIES.txt` on startup.
    - Graceful shutdown for KeyboardInterrupt and GUI exit.
    - CUDA fallback to CPU if GPU is unavailable or memory-constrained.
    - CorrelationId: 7-character identifier (e.g., `c1a2b3c`) for cross-thread log tracing.

# ♻️ Reusable Logic Registry

|Asset Name|Location|Purpose|
|---|---|---|
|FasterWhisperWrapper|`stt_engine/faster_whisper_wrapper.py`|High-performance local STT inference|
|VADLogic|`stt_engine/vad_logic.py`|Silence/Speech filtering to reduce model load|
|TransparentOverlay|`gui_overlay/overlay_window.py`|Frameless, draggable, customizable UI base|
|apply_panel_style|`gui_overlay/overlay_window.py`|VaultWares "Glass UI" styling application|

# 🚩 Tech Debt & "Watch-Outs"

    Fragile Areas: 
    - VAD Blocksize: Must remain at specific samples (512, 1024, 1536) for Silero stability.
    - Overlay mouse tracking: Draggable logic depends on `drag_handle` hitbox.

    Inconsistencies: 
    - None identified; strictly followed PySide6 and PEP8 standards.

    Future Tasks: 
    - Implement persistent config file (JSON or SQLite) for user settings.
    - Add multi-language transcription and translation toggle.

# 🕒 Change Log (Last 3 Steps)

    [2026-03-27]: Implemented granular UI controls: Color pickers and SpinBoxes. 
    - Replaced dropdowns with `QColorDialog` buttons.
    - Replaced sliders with `QSpinBox`.

    [2026-03-27]: Refined window ergonomics.
    - Added double-click to reset position above taskbar.
    - Centered control panel with `Fixed` size policy.

    [2026-03-27]: Established core engine.
    - Integrated Silero VAD and Faster-Whisper with 32ms real-time audio pipeline.
