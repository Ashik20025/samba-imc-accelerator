# SAMBA Experiment Report: smoke

## Variant Summary

| Variant | Latency Cycles | Energy pJ | Speedup | Energy Efficiency |
|---|---:|---:|---:|---:|
| puma_fixed_adc | 17,932.00 | 865,972.80 | 1.000x | 1.000x |
| sparse_puma | 17,572.00 | 315,018.00 | 1.020x | 2.749x |
| samba | 8,911.20 | 318,168.00 | 2.012x | 2.722x |

## Layer Metrics

| Layer | Variant | Windows | Blocks | Cores | Tiles | Latency | Energy | Speedup | Util. | Move Cycles | ColEx | RowEx | Split |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| tiny_conv | puma_fixed_adc | 9 | 36 | 18 | 9 | 17,932.00 | 865,972.80 | 1.000x | 100.00% | 1,192.00 | 0 | 0 | 0 |
| tiny_conv | sparse_puma | 9 | 36 | 18 | 9 | 17,572.00 | 315,018.00 | 1.020x | 85.12% | 1,192.00 | 0 | 0 | 0 |
| tiny_conv | samba | 9 | 36 | 18 | 9 | 8,911.20 | 318,168.00 | 2.012x | 85.12% | 256.00 | 0 | 0 | 0 |

## Interpretation

The fixed ADC variant models a conventional PUMA-style baseline. Sparse PUMA enables static reconfigurable ADC precision from weight sparsity. SAMBA adds compiler-time load balancing and data-movement scheduling.

The model reports architectural trends rather than transistor-calibrated silicon results. Calibrate the constants in `configs/*.json` when measured ADC, interconnect, or VFU costs are available.
