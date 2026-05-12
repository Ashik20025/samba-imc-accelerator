# Implementation Scope

## What This Project Implements

This repository implements the software-facing core of SAMBA:

1. A configurable PUMA-like analog IMC hardware model.
2. Fixed ADC and sparsity-aware reconfigurable ADC variants.
3. Crossbar MVMU partitioning for convolution and linear layers.
4. Intra-matrix load balancing:
   - Column exchange for output-column sparsity imbalance.
   - Row exchange for input-row sparsity imbalance.
5. Inter-matrix load balancing:
   - Column-wise split MVMUs for slow sparse matrices.
6. Data-movement scheduling:
   - Baseline chain reduction.
   - Tree reduction.
   - Latency-aware core sorting.
   - Input prefetch scheduling.
7. Compiler profit guard that skips load-balancing transformations when rearrange/split overhead would lose at layer level.
8. Paper-style ablation variants for each optimization family.
9. VGG19 and ResNet50 model-zoo synthetic workload generation.
10. `.npy` and `.npz` weight ingestion hooks for real trained weights.
11. Hardware design-space exploration over crossbar size, cores per tile, and MVMUs per core.
12. JSON, CSV, Markdown, trace CSV, and HTML dashboard reporting.
13. Unit tests for precision modeling, balancing, scheduling, model generation, design sweep, and report generation.

## What It Does Not Pretend To Be

This is not a transistor-level circuit simulator and does not reproduce proprietary PUMAsim internals. The timing and energy constants are explicit configuration values. That is intentional: the simulator can be calibrated later against measured ADC/interconnect/VFU costs.

## Best Next Extensions

- Add ONNX graph ingestion for trained CNNs.
- Add pruning utilities to reproduce 50% and 75% sparsity sweeps.
- Add a hardware-calibration profile with published or measured ADC costs.
- Add a PUMAsim/RTL export backend for downstream hardware validation.
