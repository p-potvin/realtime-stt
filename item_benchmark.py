import timeit
import torch

# This simulates what we actually have in vad_logic.py
def run_item():
    t = torch.tensor(0.95)
    return t.item()

def run_float():
    t = torch.tensor(0.95)
    return float(t)

if __name__ == "__main__":
    print(f".item(): {timeit.timeit(run_item, number=1000000):.4f} s")
    print(f"float(): {timeit.timeit(run_float, number=1000000):.4f} s")
