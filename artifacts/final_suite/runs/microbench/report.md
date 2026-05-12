# SAMBA Experiment Report: paper_style_microbench

## Variant Summary

| Variant | Latency Cycles | Energy pJ | Speedup | Energy Efficiency |
|---|---:|---:|---:|---:|
| puma_fixed_adc | 521,112.00 | 325,249,819.20 | 1.000x | 1.000x |
| sparse_puma | 475,464.00 | 59,909,839.20 | 1.096x | 5.429x |
| samba | 404,114.40 | 59,961,643.20 | 1.290x | 5.424x |

## Layer Metrics

| Layer | Variant | Windows | Blocks | Cores | Tiles | Latency | Energy | Speedup | Util. | Move Cycles | ColEx | RowEx | Split |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conv3x3_128_balanced70 | puma_fixed_adc | 9 | 36 | 9 | 3 | 78,052.00 | 18,069,098.40 | 1.000x | 100.00% | 448.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | puma_fixed_adc | 9 | 36 | 9 | 3 | 78,052.00 | 18,069,098.40 | 1.000x | 100.00% | 448.00 | 0 | 0 | 0 |
| conv3x3_256_unbalanced | puma_fixed_adc | 36 | 144 | 36 | 9 | 365,008.00 | 289,111,622.40 | 1.000x | 100.00% | 1,912.00 | 0 | 0 | 0 |
| conv3x3_128_balanced70 | sparse_puma | 9 | 36 | 9 | 3 | 63,652.00 | 3,606,645.60 | 1.226x | 98.83% | 336.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | sparse_puma | 9 | 36 | 9 | 3 | 73,876.00 | 3,484,857.60 | 1.057x | 92.09% | 448.00 | 0 | 0 | 0 |
| conv3x3_256_unbalanced | sparse_puma | 36 | 144 | 36 | 9 | 337,936.00 | 52,818,336.00 | 1.080x | 91.98% | 1,800.00 | 0 | 0 | 0 |
| conv3x3_128_balanced70 | samba | 9 | 43 | 11 | 3 | 61,903.20 | 3,611,037.60 | 1.261x | 99.74% | 252.00 | 0 | 0 | 7 |
| conv3x3_128_unbalanced | samba | 9 | 43 | 11 | 3 | 68,239.20 | 3,498,069.60 | 1.144x | 94.21% | 108.00 | 103 | 3 | 7 |
| conv3x3_256_unbalanced | samba | 36 | 144 | 36 | 9 | 273,972.00 | 52,852,536.00 | 1.332x | 91.98% | 52.00 | 0 | 0 | 0 |

## Interpretation

The fixed ADC variant models a conventional PUMA-style baseline. Sparse PUMA enables static reconfigurable ADC precision from weight sparsity. SAMBA adds compiler-time load balancing and data-movement scheduling.

The model reports architectural trends rather than transistor-calibrated silicon results. Calibrate the constants in `configs/*.json` when measured ADC, interconnect, or VFU costs are available.
