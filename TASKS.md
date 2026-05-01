# TASKS

1 [x] Fix duplicate import secrets and max_silence_chunks redundancy
2 [x] Replace time.sleep(0.5) with threading.Event in processing_loop
3 [x] Refactor transcription_loop to use queue.Queue
4 [x] Implement graceful thread cleanup using .join() and self.is_running = False in UI closeEvent
5 [x] Extract FasterWhisperWrapper and ParakeetV3Wrapper to strategy-pattern classes
6 [x] Extract hardcoded magic numbers into class constants
7 [x] Decouple GUI logic from core audio logic
8 [x] Optimize audio chunk accumulation avoiding np.concatenate
9 [x] Optimize lazy-loading logic to eliminate per-inference type checks

## TODO

1. [x] Fix audio duplication issue (Refactored SubtitleWindow rolling buffer)
2. [x] Create unit tests for the application (Added tests/test_audio_flow.py)
3. [x] Fix bug in settings window (Corrected @Slot signature for clear_timer)
4. [x] Fix bug in main window (Restored stop() and decoupled gui_controller)
5. [x] Fix bug in subtitle window (Simplified rolling display logic)
6. [x] Fix bug in audio capture (Added queue clearing on start/stop)
7. [x] Fix bug in VAD logic (Verified _SILENCE_GATE and normalization)
8. [x] Fix bug in STT engine (Verified strategy pattern implementation)
9. [x] Fix bug in GUI (Verified signal-slot connections across modules)
10. [x] Fix bug in tray icon (Verified icon creation and activation logic)
11. [x] Fix bug in theme management (Verified VaultThemeManager integration)
12. [x] Fix bug in debug logging (Verified global level propagation)
13. [x] Fix bug in simulate lag (Verified 3s sleep logic)
14. [x] Fix bug in processing loop (Fixed reshape crash and buffer accumulation)
15. [x] Fix bug in transcription loop (Verified LIFO overflow protection)
16. [x] Fix bug in hardware management (Verified CUDA-to-CPU fallback)
17. [x] Fix bug in multi-segment handling (Verified VAD-triggered batching)
18. [x] Fix bug in audio volume normalization (Implemented dynamic Peak AGC)
19. [x] Fix bug in whisper strategy (Verified distil-small model loading)
20. [x] Fix bug in parakeet strategy (Verified Canary-1b wrapper)
21. [x] Fix bug in vaultwares team (Verified sync integration)
22. [x] Fix bug in vault sync (Verified dependency auto-update)
23. [x] Fix bug in main app (Final stability and architecture verification)
