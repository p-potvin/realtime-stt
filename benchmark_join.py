import sys
import timeit
import tracemalloc

class Segment:
    def __init__(self, text):
        self.text = text

segments = [Segment("word " * 10) for _ in range(10000)]

def with_list_comprehension():
    l = [s.text for s in segments]
    return "".join(l).strip()

def with_generator_expression():
    return "".join(s.text for s in segments).strip()

if __name__ == "__main__":
    tracemalloc.start()
    with_list_comprehension()
    current_list, peak_list = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    with_generator_expression()
    current_gen, peak_gen = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Memory Peak - List Comprehension: {peak_list} bytes")
    print(f"Memory Peak - Generator Expression: {peak_gen} bytes")
    if peak_list > peak_gen:
         print(f"Memory Saved: {peak_list - peak_gen} bytes ({(peak_list - peak_gen) / peak_list * 100:.2f}%)")
