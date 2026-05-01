# Plan: Fix Audio Duplication and Add Unit Tests

## 1. Fix Audio Duplication in `main_app.py`

**Goal**: Resolve the issue where the same audio is processed and appended multiple times, causing system slowdown and corrupted audio.

**Changes Required**:

1. **Remove Duplicate Queue Call**: In `_run_processing_loop`,delete the second call to `self._queue_transcription(...)`.
2. **Remove Duplicate Append Call**: In `_run_processing_loop`, delete the second `self.speech_buffer.append(chunk)` that occurs when `not self.is_speaking`.
3. **Verification**: Ensure that there is only one transcription queueing operation per detected speech segment and one buffer append per input chunk.

## 2. Run Pre-Commit Checks

**Goal**: Verify the changes and ensure code quality.

**Steps**:

1. Execute the pre-commit script: `./pre_commit_instructions`.
2. Follow the instructions to format code, fix linting issues, and verify tests pass.
3. Review the generated diffs to confirm only intended changes were made.
