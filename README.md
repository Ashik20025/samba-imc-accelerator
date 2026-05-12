# SAMBA IMC Accelerator Simulator

This project implements a research-grade software model of **SAMBA: Sparsity Aware In-Memory Computing Based Machine Learning Accelerator**. It is designed as an extensible simulator for the paper's core architectural ideas:

- Sparse weight mapping onto analog IMC crossbar MVMUs.
- Reconfigurable ADC precision estimated from bit-sliced column sparsity.
- Intra-matrix load balancing with column and row exchange.
- Inter-matrix load balancing with split MVMUs.
- Data-movement optimization with allocation, tree reduction, latency-aware sort, and input prefetch scheduling.
- Paper-style component ablations.
- VGG19 and ResNet50 synthetic model-zoo workload generation for CIFAR/ImageNet-style experiments.
- Hardware design-space sweeps over crossbar size, cores per tile, and MVMUs per core.
- Reproducible latency, energy, speedup, trace, Markdown, CSV, JSON, and HTML reports.

The implementation is not a transistor-level PUMAsim replacement. It is a clean algorithmic and architectural simulator that can be extended with measured hardware constants, real model weights, or a downstream RTL/PUMAsim bridge.

## Quick Start

```bash
cd /Users/hanumanashikakshintala/Documents/New\ project/samba_imc_accelerator
PYTHONPATH=src python3 -m samba run --config configs/microbench.json --out artifacts/microbench
PYTHONPATH=src python3 -m samba run --config configs/paper_ablation.json --out artifacts/paper_ablation
PYTHONPATH=src python3 -m samba run --config configs/vgg19_cifar100_ablation.json --out artifacts/vgg19_cifar100_ablation
PYTHONPATH=src python3 -m samba run --config configs/resnet50_imagenet_profile.json --out artifacts/resnet50_imagenet_profile
PYTHONPATH=src python3 -m samba sweep --config configs/smoke.json --out artifacts/design_space_smoke --crossbar-sizes 16,32 --cores-per-tile 2,4 --mvmus-per-core 2,4
PYTHONPATH=src python3 -m unittest discover -s tests
```

Open the generated report:

```bash
open artifacts/microbench/index.html
```

## Project Layout

```text
docs/
  NON_TECHNICAL_SUMMARY.md
  TECHNICAL_DESIGN.md
  IMPLEMENTATION_SCOPE.md
  RUNBOOK.md
  RESULTS_GUIDE.md
  DASHBOARD_GUIDE.md
src/samba/
  adc.py             ADC precision, latency, and energy model
  architecture.py    Hardware and optimization configuration
  allocator.py       Baseline and SAMBA-aware MVMU-to-core packing
  balancing.py       Column exchange, row exchange, and split MVMU passes
  cli.py             Command line interface
  design_space.py    Hardware design-space sweep engine
  mapping.py         CNN/FC matrix partitioning into crossbar MVMU blocks
  reporting.py       JSON, CSV, Markdown, trace, and HTML report writers
  simulator.py       Variant orchestration and reduction scheduling
  workload.py        Synthetic microbench, model-zoo, and `.npy`/`.npz` weight loading
tests/
  test_*.py          Unit tests for ADC, balancing, scheduler, model-zoo, sweep, and CLI behavior
configs/
  microbench.json    Paper-style sparse CNN microbenchmark
  paper_ablation.json
  vgg19_cifar100_ablation.json
  resnet50_imagenet_profile.json
  full_resnet50_imagenet_75.json
```

## Main Variants

- `puma_fixed_adc`: fixed-precision ADC baseline.
- `sparse_puma`: sparsity-aware reconfigurable ADC without SAMBA balancing.
- `samba`: reconfigurable ADC plus SAMBA load balancing and data-movement scheduling.
- `paper_ablation` suite: `col_exchange`, `row_exchange`, `split_mvmu`, `load_balance_all`, `data_movement`, and `samba_full`.

## Generated Artifacts

Each `run` creates:

- `metrics.json`: complete machine-readable result object.
- `metrics.csv`: layer-level metrics for spreadsheet analysis.
- `trace.csv`: sampled instruction-level timeline events.
- `report.md`: text report for documentation.
- `index.html`: polished local dashboard with tables and SVG charts.

Each `sweep` creates:

- `design_space.csv`: all hardware points and variants.
- `design_space.md`: sweep summary and best SAMBA point.

## React Material UI Dashboard

The presentation dashboard lives in `dashboard/`. This environment has Node but no package manager, so a standalone CDN-based React + Material UI dashboard is included and can run immediately:

```bash
./scripts/start_results_dashboard.sh
```

Open `http://127.0.0.1:8088/standalone/`.

## Notes

The default hardware parameters follow the paper's examples: 64x64 MVMUs, 16-bit weights, 2 bits per slice, 16-bit streamed inputs, 4 MVMUs per core, and 4 cores per tile. Timing and energy constants are configurable so the model can be calibrated later.
