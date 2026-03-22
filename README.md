# Sphere-Cube-Center (SCC) Model Solver 🧊🌐

This repository contains the empirical proof and high-performance solvers for the **Sphere-Cube-Center Topology**, a geometric framework for polynomial preprocessing in NP-Complete problems (SAT, Hamiltonian Cycle, and Clique).

## 🚀 Performance
The C++ optimized solver uses **OpenMP** and **Boost Graph Library** to execute recursive structural transformations (the "Cube") across 20+ CPU cores, contracting the combinatorial search space (the "Sphere") *before* any brute-force search begins.

* **SAT (3-SAT):** ~82.6% reduction of the search space in polynomial time (via recursive Unit Propagation and Pure Literal cascades).
* **Hamiltonian Cycle:** ~23% reduction (via recursive degree-2 pruning).
* **Clique:** ~18% reduction (via k-core optimal polynomial contraction).

## 📂 Files in this repository
* `optimized_scc.cpp`: The scalable, multi-core industrial solver in C++.
* `np_tratable.py`: The Python simulation visualizing the Phase Transition barrier (where the "Cube" slips over the "Sphere").

## 🛠️ How to compile and run the C++ Solver (Linux / WSL / MSYS2)
You need `g++` and the Boost libraries installed.
```bash
# Compile with maximum optimization and multi-core support
g++ -O3 -fopenmp -o scc_solver optimized_scc.cpp

# Run the simulation (3000 instances)
./scc_solver
