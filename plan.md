1. *Fix Duplicate Queueing and Appending in `main_app.py`.*
   - Identify the `processing_loop` in `main_app.py`.
   - Remove the duplicate `self._queue_transcription(np.concatenate(self.speech_buffer))` call that queues the exact same audio chunk twice.
   - Remove the duplicate `self.speech_buffer.append(chunk)` call when processing silence during speech, which caused audio duplication.
2. *Run Pre-Commit Checks*
   - Execute `pre_commit_instructions` and follow the steps to ensure proper testing, verification, review, and reflection are done.
3. *Create PR*
   - Commit changes and submit to branch.
