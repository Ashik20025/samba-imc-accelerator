# Non-Technical Project Summary

## Project

This project is a software implementation of the SAMBA machine-learning accelerator idea. SAMBA improves the efficiency of AI inference by reducing unnecessary work inside memory-based computing hardware.

## Problem

Modern neural networks spend a large amount of time and energy moving data between memory and processors. In-memory computing reduces this movement by performing matrix-vector multiplication directly where model weights are stored. However, analog in-memory computing still pays a large cost when analog results are converted back into digital values using ADCs.

Many neural-network weights are zero after pruning. SAMBA uses that sparsity to lower ADC precision, rebalance uneven sparse workloads, and reduce delays from moving partial results across many compute cores.

## What This Implementation Does

The project simulates a SAMBA-style accelerator and compares three designs:

- A fixed-precision PUMA-like baseline.
- A sparse ADC baseline that lowers ADC precision when weights are sparse.
- A SAMBA design that adds load balancing and data-movement scheduling.

The simulator generates sparse convolution workloads, maps weights to crossbar compute units, estimates ADC precision, applies SAMBA optimizations, and produces latency and energy reports.

## Why It Matters

Efficient AI hardware is important for edge devices, data centers, and energy-constrained systems. A simulator like this helps evaluate accelerator ideas before committing to expensive hardware design.

## Current Result

On the included paper-style microbenchmark, SAMBA improves latency over the fixed ADC baseline while preserving most of the energy benefit from sparse ADC precision. The exact numbers are configurable because real hardware constants vary by ADC design, memory device, interconnect, and implementation process.

## Deliverables

- Source code for the simulator.
- Config files for reproducible experiments.
- Unit tests for core algorithms.
- Generated JSON, CSV, and Markdown reports.
- Documentation explaining scope, limitations, and future extensions.
