#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH=src

python3 -m unittest discover -s tests

python3 -m samba run \
  --config configs/paper_ablation.json \
  --out artifacts/paper_ablation

python3 -m samba run \
  --config configs/vgg19_cifar100_ablation.json \
  --out artifacts/vgg19_cifar100_ablation

python3 -m samba run \
  --config configs/full_resnet50_imagenet_75.json \
  --out artifacts/full_resnet50_imagenet_75

python3 -m samba sweep \
  --config configs/smoke.json \
  --out artifacts/design_space_smoke \
  --crossbar-sizes 16,32 \
  --cores-per-tile 2,4 \
  --mvmus-per-core 2,4

python3 -m samba suite \
  --configs configs/microbench.json,configs/vgg19_cifar100_ablation.json,configs/resnet50_imagenet_profile.json,configs/full_resnet50_imagenet_75.json \
  --out artifacts/final_suite

echo "Open artifacts/final_suite/index.html"
