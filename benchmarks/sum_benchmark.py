import timeit

class Chunk:
    def __init__(self, size):
        self.size = size
    def __len__(self):
        return self.size

buffer = [Chunk(512) for _ in range(100)]

def with_gen():
    return sum(len(c) for c in buffer)

def with_list():
    return sum([len(c) for c in buffer])

if __name__ == "__main__":
    t_gen = timeit.timeit(with_gen, number=100000)
    t_list = timeit.timeit(with_list, number=100000)
    print(f"Gen: {t_gen:.4f} s")
    print(f"List: {t_list:.4f} s")
