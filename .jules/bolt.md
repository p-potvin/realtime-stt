## Performance Optimization Learnings

* **Avoid I/O in Hot Paths**: Redundant file system checks (`os.path.exists`, `os.makedirs`) in frequently called STT processing loops introduce significant latency. Hoisting these checks to the initialization phase drastically reduces overhead in real-time execution.
* **Efficient Random Generation**: When generating random tokens, `secrets.token_hex(n)` is drastically more performant than concatenating multiple `secrets.choice()` calls with a list comprehension or generator expression.
* **Avoid Redundant PyTorch Clones**: In real-time PyTorch audio processing (like VAD evaluation), `.clone()` creates a full copy of the tensor. If the tensor is immediately subject to a mathematical operation that inherently creates a new tensor (e.g., `tensor / scalar`), the initial `.clone()` is a redundant memory allocation and copy that significantly degrades performance. Bypassing it provides a noticeable speedup in the hot path.
