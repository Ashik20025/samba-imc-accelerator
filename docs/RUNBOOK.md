# Runbook

## Smoke Test

```bash
cd /Users/hanumanashikakshintala/Documents/New\ project/samba_imc_accelerator
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m samba run --config configs/smoke.json --out artifacts/smoke
```

## Paper-Style Ablation

```bash
PYTHONPATH=src python3 -m samba run --config configs/paper_ablation.json --out artifacts/paper_ablation
open artifacts/paper_ablation/index.html
```

## VGG19 CIFAR-100 Profile

```bash
PYTHONPATH=src python3 -m samba run --config configs/vgg19_cifar100_ablation.json --out artifacts/vgg19_cifar100_ablation
open artifacts/vgg19_cifar100_ablation/index.html
```

## ResNet50 ImageNet Profile

```bash
PYTHONPATH=src python3 -m samba run --config configs/resnet50_imagenet_profile.json --out artifacts/resnet50_imagenet_profile
open artifacts/resnet50_imagenet_profile/index.html
```

The `resnet50_imagenet_profile.json` config limits the model-zoo run to the first 12 layers so iteration is fast. Use `configs/full_resnet50_imagenet_75.json` for all generated ResNet50 convolution/projection layers.

## Design-Space Sweep

```bash
PYTHONPATH=src python3 -m samba sweep \
  --config configs/smoke.json \
  --out artifacts/design_space_smoke \
  --crossbar-sizes 16,32 \
  --cores-per-tile 2,4 \
  --mvmus-per-core 2,4
```

## Real Weights

For an explicit layer, set `weights_path` and optionally `weights_key` in the config. The simulator accepts `.npy` and `.npz` tensors. Convolution tensors are expected as `(kernel_h, kernel_w, in_channels, out_channels)` and linear tensors as `(in_features, out_features)`.
