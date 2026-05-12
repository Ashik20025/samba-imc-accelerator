# SAMBA Experiment Report: resnet50_imagenet_75pct_sparse

## Variant Summary

| Variant | Latency Cycles | Energy pJ | Speedup | Energy Efficiency |
|---|---:|---:|---:|---:|
| puma_fixed_adc | 396,352,384.00 | 44,771,422,617.60 | 1.000x | 1.000x |
| sparse_puma | 297,706,368.00 | 3,306,600,908.80 | 1.331x | 13.540x |
| samba | 280,082,403.20 | 3,316,505,651.20 | 1.415x | 13.500x |

## Layer Metrics

| Layer | Variant | Windows | Blocks | Cores | Tiles | Latency | Energy | Speedup | Util. | Move Cycles | ColEx | RowEx | Split |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| resnet50_stem_7x7 | puma_fixed_adc | 12544 | 49 | 13 | 4 | 111,641,568.00 | 34,279,595,929.60 | 1.000x | 100.00% | 672.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv1_1x1 | puma_fixed_adc | 3136 | 1 | 1 | 1 | 25,802,976.00 | 174,843,289.60 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv2_3x3 | puma_fixed_adc | 3136 | 9 | 3 | 1 | 26,053,856.00 | 1,573,940,838.40 | 1.000x | 100.00% | 80.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv3_1x1 | puma_fixed_adc | 3136 | 4 | 1 | 1 | 25,802,976.00 | 699,373,158.40 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b1_projection_1x1 | puma_fixed_adc | 3136 | 4 | 1 | 1 | 25,802,976.00 | 699,373,158.40 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b2_conv1_1x1 | puma_fixed_adc | 3136 | 4 | 1 | 1 | 25,802,976.00 | 699,373,158.40 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b2_conv2_3x3 | puma_fixed_adc | 3136 | 9 | 3 | 1 | 26,053,856.00 | 1,573,940,838.40 | 1.000x | 100.00% | 80.00 | 0 | 0 | 0 |
| resnet50_s2_b2_conv3_1x1 | puma_fixed_adc | 3136 | 4 | 1 | 1 | 25,802,976.00 | 699,373,158.40 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b3_conv1_1x1 | puma_fixed_adc | 3136 | 4 | 1 | 1 | 25,802,976.00 | 699,373,158.40 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b3_conv2_3x3 | puma_fixed_adc | 3136 | 9 | 3 | 1 | 26,053,856.00 | 1,573,940,838.40 | 1.000x | 100.00% | 80.00 | 0 | 0 | 0 |
| resnet50_s2_b3_conv3_1x1 | puma_fixed_adc | 3136 | 4 | 1 | 1 | 25,802,976.00 | 699,373,158.40 | 1.000x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s3_b1_conv1_1x1 | puma_fixed_adc | 3136 | 8 | 2 | 1 | 25,928,416.00 | 1,398,921,932.80 | 1.000x | 100.00% | 40.00 | 0 | 0 | 0 |
| resnet50_stem_7x7 | sparse_puma | 12544 | 49 | 13 | 4 | 38,183,904.00 | 1,183,897,702.40 | 2.924x | 74.09% | 480.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv1_1x1 | sparse_puma | 3136 | 1 | 1 | 1 | 23,394,528.00 | 39,488,512.00 | 1.103x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv2_3x3 | sparse_puma | 3136 | 9 | 3 | 1 | 23,695,584.00 | 295,142,758.40 | 1.100x | 94.13% | 80.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv3_1x1 | sparse_puma | 3136 | 4 | 1 | 1 | 23,545,056.00 | 150,703,616.00 | 1.096x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b1_projection_1x1 | sparse_puma | 3136 | 4 | 1 | 1 | 23,645,408.00 | 150,959,513.60 | 1.091x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b2_conv1_1x1 | sparse_puma | 3136 | 4 | 1 | 1 | 23,444,704.00 | 148,016,691.20 | 1.101x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b2_conv2_3x3 | sparse_puma | 3136 | 9 | 3 | 1 | 23,996,640.00 | 295,185,408.00 | 1.086x | 93.14% | 80.00 | 0 | 0 | 0 |
| resnet50_s2_b2_conv3_1x1 | sparse_puma | 3136 | 4 | 1 | 1 | 23,394,528.00 | 150,234,470.40 | 1.103x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b3_conv1_1x1 | sparse_puma | 3136 | 4 | 1 | 1 | 23,595,232.00 | 149,040,281.60 | 1.094x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b3_conv2_3x3 | sparse_puma | 3136 | 9 | 3 | 1 | 23,745,760.00 | 294,588,313.60 | 1.097x | 93.92% | 80.00 | 0 | 0 | 0 |
| resnet50_s2_b3_conv3_1x1 | sparse_puma | 3136 | 4 | 1 | 1 | 23,494,880.00 | 151,471,308.80 | 1.098x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s3_b1_conv1_1x1 | sparse_puma | 3136 | 8 | 2 | 1 | 23,570,144.00 | 297,872,332.80 | 1.100x | 99.68% | 40.00 | 0 | 0 | 0 |
| resnet50_stem_7x7 | samba | 12544 | 54 | 14 | 4 | 27,325,847.20 | 1,191,373,926.40 | 4.086x | 75.02% | 120.00 | 0 | 0 | 5 |
| resnet50_s2_b1_conv1_1x1 | samba | 3136 | 1 | 1 | 1 | 23,301,732.00 | 39,488,512.00 | 1.107x | 100.00% | 0.00 | 0 | 0 | 0 |
| resnet50_s2_b1_conv2_3x3 | samba | 3136 | 10 | 3 | 1 | 22,498,916.00 | 295,199,206.40 | 1.158x | 97.39% | 12.00 | 0 | 0 | 1 |
| resnet50_s2_b1_conv3_1x1 | samba | 3136 | 4 | 1 | 1 | 23,075,940.00 | 150,816,512.00 | 1.118x | 100.00% | 0.00 | 3 | 0 | 0 |
| resnet50_s2_b1_projection_1x1 | samba | 3136 | 4 | 1 | 1 | 23,276,644.00 | 151,072,409.60 | 1.109x | 100.00% | 0.00 | 3 | 0 | 0 |
| resnet50_s2_b2_conv1_1x1 | samba | 3136 | 4 | 1 | 1 | 22,925,412.00 | 149,067,878.40 | 1.126x | 100.00% | 0.00 | 0 | 6 | 0 |
| resnet50_s2_b2_conv2_3x3 | samba | 3136 | 10 | 3 | 1 | 22,473,828.00 | 295,241,856.00 | 1.159x | 96.72% | 4.00 | 0 | 0 | 1 |
| resnet50_s2_b2_conv3_1x1 | samba | 3136 | 4 | 1 | 1 | 23,226,468.00 | 150,347,366.40 | 1.111x | 100.00% | 0.00 | 1 | 0 | 0 |
| resnet50_s2_b3_conv1_1x1 | samba | 3136 | 4 | 1 | 1 | 23,126,116.00 | 149,451,724.80 | 1.116x | 100.00% | 0.00 | 0 | 3 | 0 |
| resnet50_s2_b3_conv2_3x3 | samba | 3136 | 10 | 3 | 1 | 22,423,652.00 | 294,644,761.60 | 1.162x | 96.71% | 4.00 | 0 | 0 | 1 |
| resnet50_s2_b3_conv3_1x1 | samba | 3136 | 4 | 1 | 1 | 23,326,820.00 | 151,584,204.80 | 1.106x | 100.00% | 0.00 | 1 | 0 | 0 |
| resnet50_s3_b1_conv1_1x1 | samba | 3136 | 9 | 3 | 1 | 23,101,028.00 | 298,217,292.80 | 1.122x | 82.69% | 4.00 | 3 | 0 | 1 |

## Interpretation

The fixed ADC variant models a conventional PUMA-style baseline. Sparse PUMA enables static reconfigurable ADC precision from weight sparsity. SAMBA adds compiler-time load balancing and data-movement scheduling.

The model reports architectural trends rather than transistor-calibrated silicon results. Calibrate the constants in `configs/*.json` when measured ADC, interconnect, or VFU costs are available.
