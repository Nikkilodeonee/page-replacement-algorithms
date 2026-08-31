# Page Replacement Simulation: FIFO vs MFU

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

Coursework project from Operating Systems: a small simulator that compares **FIFO** and **MFU** page replacement under different sequence lengths, frame counts, and locality.

## Overview

The program generates page-access sequences with a locality factor, counts page faults, averages a few repetitions, and plots the results with Matplotlib.

## Algorithms

### FIFO (First In First Out)

Evicts the oldest page in memory. Simple and predictable; ignores how often a page is used.

### MFU (Most Frequently Used)

Evicts the page with the highest access count, on the idea that it has already “served its purpose.” That can remove pages that are still hot, so MFU often does worse than FIFO when locality is high.

## Run

```bash
pip install -r requirements.txt
python main.py
```

This prints three comparison tables and opens bar charts for:

- sequence length
- number of frames
- locality factor

Parameters live at the bottom of `main.py`.

## Example charts

<img width="1242" height="748" alt="FIFO vs MFU by sequence length" src="https://github.com/user-attachments/assets/8f3d7733-44ff-4ceb-9498-a4f824696bd1" />
<img width="1251" height="749" alt="FIFO vs MFU by frame count" src="https://github.com/user-attachments/assets/cd9613ad-598a-45f7-854d-857badb72bd0" />
<img width="1246" height="748" alt="FIFO vs MFU by locality" src="https://github.com/user-attachments/assets/50aa6f91-eb7c-4751-b1b7-7fca83837dd3" />

FIFO is simpler and usually better here. More frames reduce faults for both algorithms.

## License

MIT. Author: [Roman Sushkin](https://github.com/Nikkilodeonee)
