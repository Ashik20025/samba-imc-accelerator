# Results Guide

## What The Project Shows

The project shows that a SAMBA-style analog in-memory-computing accelerator can reduce neural-network inference latency and energy compared with a fixed-ADC PUMA-style baseline.

The main comparison is:

1. `puma_fixed_adc`: conventional fixed-precision ADC baseline.
2. `sparse_puma`: sparse weights reduce ADC precision.
3. `samba` / `samba_full`: sparse ADC plus load balancing and optimized data movement.

## Best Page To Open

Open:

```bash
open artifacts/final_suite/index.html
```

This aggregate dashboard is the cleanest page for presentation.

## Strongest Result

Use the full ResNet50 ImageNet-style run:

- Fixed ADC baseline: `524,069,964` cycles.
- Sparse ADC baseline: `417,330,324` cycles.
- SAMBA: `387,806,217.60` cycles.
- Speedup over fixed ADC: `1.351x`.
- Energy-efficiency improvement over fixed ADC: about `7.36x`.

## What The Ablation Shows

The ablation result explains the engineering story:

- Sparse ADC gives a large energy reduction.
- Data-movement optimization is critical for large convolution workloads.
- Split MVMU can help by dividing slow dense columns.
- Column/row exchange can hurt if rearrange overhead is too high.
- Full SAMBA uses a compiler profit guard to skip transformations that do not pay off.

## Honest Scope Statement

This is a software architectural simulator, not a fabricated chip, RTL implementation, or transistor-level PUMAsim reproduction. It is still a solid project because it implements the paper's mapping, balancing, scheduling, reporting, and design-space workflow in a reproducible codebase.

## One-Minute Explanation

Neural networks use many matrix-vector multiplications. In analog in-memory computing, those multiplications happen inside memory crossbars, but the outputs must pass through ADCs. ADCs cost time and energy. SAMBA uses sparsity to lower ADC precision, balances uneven sparse workloads, and schedules data movement better across cores and tiles. In this simulator, those ideas reduce cycles and energy on VGG19 and ResNet50-style workloads.
