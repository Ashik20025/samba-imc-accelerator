# SAMBA Experiment Report: paper_component_ablation_microbench

## Variant Summary

| Variant | Latency Cycles | Energy pJ | Speedup | Energy Efficiency |
|---|---:|---:|---:|---:|
| puma_fixed_adc | 738,840.00 | 1,192,596,134.40 | 1.000x | 1.000x |
| sparse_puma | 694,020.00 | 218,304,079.20 | 1.065x | 5.463x |
| col_exchange | 1,293,708.00 | 219,221,971.20 | 0.571x | 5.440x |
| row_exchange | 694,884.00 | 218,322,756.00 | 1.063x | 5.463x |
| split_mvmu | 748,560.00 | 218,455,747.20 | 0.987x | 5.459x |
| load_balance_all | 1,354,440.00 | 219,394,101.60 | 0.545x | 5.436x |
| data_movement | 413,150.40 | 218,477,329.20 | 1.788x | 5.459x |
| samba_full | 413,150.40 | 218,477,329.20 | 1.788x | 5.459x |

## Layer Metrics

| Layer | Variant | Windows | Blocks | Cores | Tiles | Latency | Energy | Speedup | Util. | Move Cycles | ColEx | RowEx | Split |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| conv3x3_128_balanced70 | puma_fixed_adc | 9 | 36 | 9 | 3 | 78,052.00 | 18,069,098.40 | 1.000x | 100.00% | 448.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | puma_fixed_adc | 9 | 36 | 9 | 3 | 78,052.00 | 18,069,098.40 | 1.000x | 100.00% | 448.00 | 0 | 0 | 0 |
| conv3x3_512_unbalanced | puma_fixed_adc | 36 | 576 | 144 | 36 | 582,736.00 | 1,156,457,937.60 | 1.000x | 100.00% | 7,960.00 | 0 | 0 | 0 |
| conv3x3_128_balanced70 | sparse_puma | 9 | 36 | 9 | 3 | 64,048.00 | 3,607,012.80 | 1.219x | 98.34% | 348.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | sparse_puma | 9 | 36 | 9 | 3 | 73,156.00 | 3,480,818.40 | 1.067x | 93.10% | 448.00 | 0 | 0 | 0 |
| conv3x3_512_unbalanced | sparse_puma | 36 | 576 | 144 | 36 | 556,816.00 | 211,216,248.00 | 1.047x | 92.21% | 7,896.00 | 0 | 0 | 0 |
| conv3x3_128_balanced70 | col_exchange | 9 | 36 | 9 | 3 | 64,048.00 | 3,607,012.80 | 1.219x | 98.34% | 348.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | col_exchange | 9 | 36 | 9 | 3 | 74,668.00 | 3,485,030.40 | 1.045x | 91.24% | 448.00 | 119 | 0 | 0 |
| conv3x3_512_unbalanced | col_exchange | 36 | 576 | 144 | 36 | 1,154,992.00 | 212,129,928.00 | 0.505x | 85.64% | 7,944.00 | 2869 | 0 | 0 |
| conv3x3_128_balanced70 | row_exchange | 9 | 36 | 9 | 3 | 64,048.00 | 3,607,012.80 | 1.219x | 98.34% | 348.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | row_exchange | 9 | 36 | 9 | 3 | 74,020.00 | 3,499,495.20 | 1.054x | 92.45% | 448.00 | 0 | 13 | 0 |
| conv3x3_512_unbalanced | row_exchange | 36 | 576 | 144 | 36 | 556,816.00 | 211,216,248.00 | 1.047x | 92.21% | 7,896.00 | 0 | 0 | 0 |
| conv3x3_128_balanced70 | split_mvmu | 9 | 43 | 11 | 3 | 64,336.00 | 3,609,154.80 | 1.213x | 99.65% | 496.00 | 0 | 0 | 7 |
| conv3x3_128_unbalanced | split_mvmu | 9 | 43 | 11 | 3 | 69,664.00 | 3,482,960.40 | 1.120x | 91.67% | 528.00 | 0 | 0 | 7 |
| conv3x3_512_unbalanced | split_mvmu | 36 | 691 | 173 | 44 | 614,560.00 | 211,363,632.00 | 0.948x | 92.12% | 9,520.00 | 0 | 0 | 115 |
| conv3x3_128_balanced70 | load_balance_all | 9 | 43 | 11 | 3 | 64,336.00 | 3,609,154.80 | 1.213x | 99.65% | 496.00 | 0 | 0 | 7 |
| conv3x3_128_unbalanced | load_balance_all | 9 | 43 | 11 | 3 | 73,336.00 | 3,507,634.80 | 1.064x | 93.76% | 480.00 | 119 | 13 | 7 |
| conv3x3_512_unbalanced | load_balance_all | 36 | 691 | 173 | 44 | 1,216,768.00 | 212,277,312.00 | 0.479x | 86.25% | 9,600.00 | 2869 | 0 | 115 |
| conv3x3_128_balanced70 | data_movement | 9 | 36 | 9 | 3 | 61,615.20 | 3,607,912.80 | 1.267x | 98.34% | 104.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | data_movement | 9 | 36 | 9 | 3 | 68,923.20 | 3,482,168.40 | 1.132x | 93.10% | 4.00 | 0 | 0 | 0 |
| conv3x3_512_unbalanced | data_movement | 36 | 576 | 144 | 36 | 282,612.00 | 211,387,248.00 | 2.062x | 92.21% | 308.00 | 0 | 0 | 0 |
| conv3x3_128_balanced70 | samba_full | 9 | 36 | 9 | 3 | 61,615.20 | 3,607,912.80 | 1.267x | 98.34% | 104.00 | 0 | 0 | 0 |
| conv3x3_128_unbalanced | samba_full | 9 | 36 | 9 | 3 | 68,923.20 | 3,482,168.40 | 1.132x | 93.10% | 4.00 | 0 | 0 | 0 |
| conv3x3_512_unbalanced | samba_full | 36 | 576 | 144 | 36 | 282,612.00 | 211,387,248.00 | 2.062x | 92.21% | 308.00 | 0 | 0 | 0 |

## Interpretation

The fixed ADC variant models a conventional PUMA-style baseline. Sparse PUMA enables static reconfigurable ADC precision from weight sparsity. SAMBA adds compiler-time load balancing and data-movement scheduling.

The model reports architectural trends rather than transistor-calibrated silicon results. Calibrate the constants in `configs/*.json` when measured ADC, interconnect, or VFU costs are available.
