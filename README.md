# Page Replacement Simulation: FIFO vs MFU

![Python](https://img.shields.io/badge/Python-3.10-blue.svg)  
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview
This project implements and compares two fundamental **page replacement algorithms** used in memory management:
- **FIFO (First In First Out)**
- **MFU (Most Frequently Used)**

The program simulates memory accesses with controlled locality, evaluates page faults and hits, and visualizes results with **Matplotlib**.

---

## Key Features
- Simulation of **page replacement** with configurable parameters.  
- Modular object-oriented design with reusable classes.  
- Experiments with:
  - Sequence length  
  - Number of frames  
  - Locality factor  
- Tabular results with per-experiment page fault counts.  
- Side-by-side **bar chart comparisons** of FIFO vs MFU.  

---

## Algorithms Explained

### FIFO (First In First Out)
- **Description**: Replaces the page that has been in memory the longest (oldest).  
- **Pros**: Very simple, predictable.  
- **Cons**: Ignores frequency/locality of access, may cause many page faults.  

### MFU (Most Frequently Used)
- **Description**: Removes the page with the **highest access count**, assuming it has “served its purpose.”  
- **Pros**: Tries to discard overused pages.  
- **Cons**: Counterintuitive — may remove pages still needed, often worse than FIFO in practice.  

---

## Code Structure
- **`PageReplacementSimulator`** – base class (frames, stats, abstract access method).  
- **`FIFO`** – queue-based page replacement strategy.  
- **`MFU`** – frequency-based page replacement strategy.  
- **`generate_page_sequence()`** – creates random page access sequences with adjustable locality.  
- **`run_experiment()`** – runs controlled experiments, averages results.  
- **`plot_results()`** – visualization of comparisons.  
- **`print_table()`** – formatted tabular results.  

---

## Getting Started

### Install dependencies
```bash
pip install matplotlib numpy
```

### Run the simulation
```bash
python main.py
```

This will:
- Print page fault comparison tables in the console.  
- Show bar charts comparing **FIFO** and **MFU** results.  

---

## Customization
You can adjust:
- **Sequence length**  
- **Number of frames**  
- **Locality factor**  
- **Repetitions** for averaging  

---

<img width="1242" height="748" alt="image" src="https://github.com/user-attachments/assets/8f3d7733-44ff-4ceb-9498-a4f824696bd1" />
<img width="1251" height="749" alt="image" src="https://github.com/user-attachments/assets/cd9613ad-598a-45f7-854d-857badb72bd0" />
<img width="1246" height="748" alt="image" src="https://github.com/user-attachments/assets/50aa6f91-eb7c-4751-b1b7-7fca83837dd3" />

---

## Conclusion
- **FIFO** is simple and generally performs better in practice.  
- **MFU** can perform worse under high locality due to its replacement policy.  
- Increasing the **number of frames** reduces page faults for both algorithms.  

---

## License
This project is licensed under the MIT License.

## Author
Nikkilodeonee 
