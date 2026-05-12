# SAMBA Final Suite Executive Summary

## Main Claim

The simulator evaluates a PUMA-style fixed ADC baseline, a sparse reconfigurable ADC baseline, and SAMBA optimizations for sparse analog in-memory-computing inference.

## Headline Results

| Experiment | Best SAMBA Variant | Layers | Speedup | Energy Efficiency | Report |
|---|---|---:|---:|---:|---|
| full_resnet50_imagenet_75 (resnet50_imagenet_75pct_sparse) | samba | 53 | 1.351x | 7.361x | [open](/Users/hanumanashikakshintala/Documents/New project/samba_imc_accelerator/artifacts/final_suite/runs/full_resnet50_imagenet_75/index.html) |
| microbench (paper_style_microbench) | samba | 3 | 1.290x | 5.424x | [open](/Users/hanumanashikakshintala/Documents/New project/samba_imc_accelerator/artifacts/final_suite/runs/microbench/index.html) |
| resnet50_imagenet_profile (resnet50_imagenet_75pct_sparse) | samba | 12 | 1.415x | 13.500x | [open](/Users/hanumanashikakshintala/Documents/New project/samba_imc_accelerator/artifacts/final_suite/runs/resnet50_imagenet_profile/index.html) |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | samba_full | 8 | 1.604x | 6.141x | [open](/Users/hanumanashikakshintala/Documents/New project/samba_imc_accelerator/artifacts/final_suite/runs/vgg19_cifar100_ablation/index.html) |

## Full Variant Table

| Experiment | Variant | Latency Cycles | Energy pJ | Speedup | Energy Eff. |
|---|---|---:|---:|---:|---:|
| microbench (paper_style_microbench) | puma_fixed_adc | 521,112.00 | 325,249,819.20 | 1.000x | 1.000x |
| microbench (paper_style_microbench) | sparse_puma | 475,464.00 | 59,909,839.20 | 1.096x | 5.429x |
| microbench (paper_style_microbench) | samba | 404,114.40 | 59,961,643.20 | 1.290x | 5.424x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | puma_fixed_adc | 23,932,672.00 | 3,597,742,899.20 | 1.000x | 1.000x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | sparse_puma | 16,358,144.00 | 585,473,689.60 | 1.463x | 6.145x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | col_exchange | 16,840,960.00 | 586,365,337.60 | 1.421x | 6.136x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | row_exchange | 16,413,440.00 | 586,558,464.00 | 1.458x | 6.134x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | split_mvmu | 15,636,736.00 | 585,776,793.60 | 1.531x | 6.142x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | load_balance_all | 16,130,304.00 | 587,376,844.80 | 1.484x | 6.125x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | data_movement | 15,549,011.20 | 585,700,889.60 | 1.539x | 6.143x |
| vgg19_cifar100_ablation (vgg19_cifar100_75pct_sparse) | samba_full | 14,916,179.20 | 585,861,657.60 | 1.604x | 6.141x |
| resnet50_imagenet_profile (resnet50_imagenet_75pct_sparse) | puma_fixed_adc | 396,352,384.00 | 44,771,422,617.60 | 1.000x | 1.000x |
| resnet50_imagenet_profile (resnet50_imagenet_75pct_sparse) | sparse_puma | 297,706,368.00 | 3,306,600,908.80 | 1.331x | 13.540x |
| resnet50_imagenet_profile (resnet50_imagenet_75pct_sparse) | samba | 280,082,403.20 | 3,316,505,651.20 | 1.415x | 13.500x |
| full_resnet50_imagenet_75 (resnet50_imagenet_75pct_sparse) | puma_fixed_adc | 524,069,964.00 | 88,319,369,782.00 | 1.000x | 1.000x |
| full_resnet50_imagenet_75 (resnet50_imagenet_75pct_sparse) | sparse_puma | 417,330,324.00 | 11,983,397,762.00 | 1.256x | 7.370x |
| full_resnet50_imagenet_75 (resnet50_imagenet_75pct_sparse) | samba | 387,806,217.60 | 11,998,902,361.60 | 1.351x | 7.361x |

## Validation

- `ok` `suite`: All sanity checks passed.

## What To Show

1. Start with this executive summary.
2. Open the full ResNet50 dashboard for the largest workload.
3. Open the VGG19 ablation dashboard to explain which SAMBA components help.
4. Show `trace.csv` to demonstrate the project models core/tile execution, not only final numbers.
