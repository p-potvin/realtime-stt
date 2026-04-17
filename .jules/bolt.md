## 2023-10-24 - Double Processing Bottleneck
**Learning:** Found a copy-paste error in the main audio processing loop (`main_app.py`) where identical audio chunks were being queued for transcription TWICE, effectively halving STT throughput. Additionally, silence chunks were appended twice, artificially lengthening the audio buffer and wasting memory/processing time.
**Action:** Always verify loop accumulation and queueing logic, especially when sliding windows are involved. Ensure that buffers are not redundantly appended or passed to expensive ML tasks.
