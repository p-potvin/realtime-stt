import timeit

setup_code = """
class Segment:
    def __init__(self, text):
        self.text = text

segments = [Segment("This is a somewhat longer text to simulate real world transcriptions. ") for _ in range(1000)]
"""

gen_code = 'text = "".join(s.text for s in segments).strip()'
list_code = 'text = "".join([s.text for s in segments]).strip()'

gen_time = timeit.timeit(gen_code, setup=setup_code, number=10000)
list_time = timeit.timeit(list_code, setup=setup_code, number=10000)

print(f"Generator expression (large): {gen_time:.4f} seconds")
print(f"List comprehension (large): {list_time:.4f} seconds")
