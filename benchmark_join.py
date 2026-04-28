import timeit

setup_code = """
class Segment:
    def __init__(self, text):
        self.text = text

segments = [Segment("hello ") for _ in range(100)]
"""

gen_code = 'text = "".join(s.text for s in segments).strip()'
list_code = 'text = "".join([s.text for s in segments]).strip()'

gen_time = timeit.timeit(gen_code, setup=setup_code, number=100000)
list_time = timeit.timeit(list_code, setup=setup_code, number=100000)

print(f"Generator expression: {gen_time:.4f} seconds")
print(f"List comprehension: {list_time:.4f} seconds")
