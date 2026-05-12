# Technical Design

## Pipeline

1. Parse an experiment configuration.
2. Generate or load sparse neural-network layer weights.
3. Partition each matrix into crossbar-sized MVMU blocks.
4. Estimate fixed or reconfigurable ADC precision per bit-slice column.
5. Optionally apply SAMBA load-balancing passes.
6. Run a compiler profit guard when full SAMBA is enabled.
7. Allocate MVMUs to cores and tiles.
8. Simulate MVM latency, reduction latency, movement cost, and energy.
9. Emit machine-readable and human-readable reports.

## SAMBA Passes

### Column Exchange

Columns from slow, dense MVMUs are swapped with cheaper columns from faster, sparse MVMUs that share the same input vector. This targets the ADC bottleneck because ADC precision is determined column-wise.

### Row Exchange

Dense input rows are swapped with sparse rows across row-block groups. This balances MVMUs where uneven row utilization causes one block to dominate the shared instruction latency.

### Split MVMU

Slow MVMUs can be split column-wise into two parallel MVMUs. The simulator greedily balances column ADC cost across the two children and accounts for the extra ALU merge cost.

### Data Movement

The simulator supports baseline linear accumulation and SAMBA-style tree reduction with latency-aware sorting. It also models input prefetch scheduling for convolution windows.

### Compiler Profit Guard

The paper notes that load balancing can hurt large layers if rearrange or split overhead dominates. Full SAMBA therefore evaluates both the transformed layer and the untransformed layer under the same movement schedule, then keeps the lower-latency plan. Raw component ablations intentionally disable this guard so the tradeoff is visible.

## Workloads

The workload engine supports:

- Explicit convolution and linear layers from JSON.
- Synthetic balanced or unbalanced sparsity.
- VGG19 model-zoo generation for CIFAR/ImageNet-style inputs.
- ResNet50 model-zoo generation for CIFAR/ImageNet-style inputs.
- `.npy` and `.npz` weight loading for real trained layer tensors.

## Outputs

The reporting layer writes `metrics.json`, `metrics.csv`, `trace.csv`, `report.md`, and `index.html`. The trace is a sampled instruction-level timeline with MVM, reduction, rearrange, and split-merge events.

## Calibration

Timing and energy constants live in JSON configs. The default values are intentionally transparent. For more accurate research results, calibrate:

- ADC cycle and energy per bit.
- Load/store/send/receive cycles.
- VFU rearrange cost.
- Shift-and-add cost.
- Memory device and peripheral energy.
