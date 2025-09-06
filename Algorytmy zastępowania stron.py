import random
from collections import deque, defaultdict
import matplotlib.pyplot as plt
import numpy as np


class PageReplacementSimulator:
    def __init__(self, num_frames):
        self.num_frames = num_frames
        self.page_faults = 0
        self.page_hits = 0

    def access_page(self, page):
        raise NotImplementedError


class FIFO(PageReplacementSimulator):
    def __init__(self, num_frames):
        super().__init__(num_frames)
        self.queue = deque()
        self.memory = set()

    def access_page(self, page):
        if page in self.memory:
            self.page_hits += 1
        else:
            self.page_faults += 1
            if len(self.memory) >= self.num_frames:
                removed = self.queue.popleft()
                self.memory.remove(removed)
            self.queue.append(page)
            self.memory.add(page)


class MFU(PageReplacementSimulator):
    def __init__(self, num_frames):
        super().__init__(num_frames)
        self.memory = set()
        self.usage_count = defaultdict(int)

    def access_page(self, page):
        self.usage_count[page] += 1
        if page in self.memory:
            self.page_hits += 1
        else:
            self.page_faults += 1
            if len(self.memory) >= self.num_frames:
                most_used = max(self.memory, key=lambda p: self.usage_count[p])
                self.memory.remove(most_used)
            self.memory.add(page)


def generate_page_sequence(length, page_range=10, locality_factor=0.5):
    sequence = []
    current_page = random.randint(0, page_range - 1)
    for _ in range(length):
        if random.random() < locality_factor:
            delta = random.choice([-1, 0, 1])
            current_page = max(0, min(page_range - 1, current_page + delta))
        else:
            current_page = random.randint(0, page_range - 1)
        sequence.append(current_page)
    return sequence


def run_experiment(vary_values, fixed_param, param_type, repetitions=5, page_range=10):
    fifo_results = []
    mfu_results = []

    for value in vary_values:
        fifo_total = 0
        mfu_total = 0

        for _ in range(repetitions):
            if param_type == "length":
                sequence = generate_page_sequence(value, page_range, fixed_param)
                num_frames = 3
            elif param_type == "frames":
                sequence = generate_page_sequence(200, page_range, fixed_param)
                num_frames = value
            elif param_type == "locality":
                sequence = generate_page_sequence(200, page_range, value)
                num_frames = 3

            fifo = FIFO(num_frames)
            mfu = MFU(num_frames)

            for page in sequence:
                fifo.access_page(page)
                mfu.access_page(page)

            fifo_total += fifo.page_faults
            mfu_total += mfu.page_faults

        fifo_results.append(int(fifo_total / repetitions))
        mfu_results.append(int(mfu_total / repetitions))

    return vary_values, fifo_results, mfu_results


def plot_results(x_vals, fifo_vals, mfu_vals, xlabel, title):
    x = np.arange(len(x_vals))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width/2, fifo_vals, width, label='FIFO', color='skyblue')
    ax.bar(x + width/2, mfu_vals, width, label='MFU', color='salmon')

    ax.set_ylabel('Liczba błędów strony')
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels([str(v) for v in x_vals])
    ax.legend()
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()


def print_table(title, column_name, x_vals, fifo_vals, mfu_vals):
    print(f"\n{title}")
    print(f"{column_name:<20} {'FIFO - błędy':<15} {'MFU - błędy':<15}")
    for i in range(len(x_vals)):
        print(f"{str(x_vals[i]):<20} {str(fifo_vals[i]):<15} {str(mfu_vals[i]):<15}")


# Eksperyment 1: różna długość sekwencji
lengths = [50, 100, 150, 200, 250]
x1, fifo1, mfu1 = run_experiment(lengths, fixed_param=0.6, param_type="length")
plot_results(x1, fifo1, mfu1, "Długość sekwencji", "Porównanie FIFO i MFU dla różnych długości sekwencji\n(ramki=3, lokalność=0.6, strony=0-9)")
print_table("Porównanie FIFO i MFU dla różnych długości sekwencji", "Długość sekwencji", x1, fifo1, mfu1)

# Eksperyment 2: różna liczba ramek
frames = [2, 3, 4, 5, 6]
x2, fifo2, mfu2 = run_experiment(frames, fixed_param=0.6, param_type="frames")
plot_results(x2, fifo2, mfu2, "Liczba ramek", "Porównanie FIFO i MFU dla różnej liczby ramek\n(sekwencja=200, lokalność=0.6, strony=0-9)")
print_table("Porównanie dla różnej liczby ramek", "Liczba ramek", x2, fifo2, mfu2)

# Eksperyment 3: różny poziom lokalności
localities = [0.1, 0.3, 0.5, 0.7, 0.9]
x3, fifo3, mfu3 = run_experiment(localities, fixed_param=3, param_type="locality")
plot_results(x3, fifo3, mfu3, "Poziom lokalności", "Porównanie FIFO i MFU dla różnych poziomów lokalności\n(ramki=3, sekwencja=200, strony=0-9)")
print_table("Porównanie dla różnych poziomów lokalności", "Poziom lokalności", x3, fifo3, mfu3)
