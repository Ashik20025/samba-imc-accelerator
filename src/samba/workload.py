"""Workload definitions and synthetic model generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class LayerSpec:
    name: str
    type: str
    weights: np.ndarray
    input_h: int | None = None
    input_w: int | None = None
    stride: int = 1
    padding: int = 0
    metadata: dict[str, object] | None = None

    @property
    def is_conv(self) -> bool:
        return self.type == "conv2d"

    @property
    def windows(self) -> int:
        if not self.is_conv:
            return 1
        if self.input_h is None or self.input_w is None:
            raise ValueError(f"Convolution layer {self.name} requires input_h/input_w")
        kh, kw = self.weights.shape[:2]
        out_h = ((self.input_h + 2 * self.padding - kh) // self.stride) + 1
        out_w = ((self.input_w + 2 * self.padding - kw) // self.stride) + 1
        return max(1, out_h * out_w)


@dataclass(frozen=True)
class Workload:
    name: str
    layers: tuple[LayerSpec, ...]


def _apply_sparsity(values: np.ndarray, sparsity: float, rng: np.random.Generator) -> np.ndarray:
    mask = rng.random(values.shape) >= sparsity
    return values * mask


def _balanced_weights(
    shape: tuple[int, ...],
    sparsity: float,
    rng: np.random.Generator,
    *,
    max_weight: int,
) -> np.ndarray:
    values = rng.integers(1, max_weight + 1, size=shape, dtype=np.int32)
    return _apply_sparsity(values, sparsity, rng).astype(np.int32)


def _load_weights(path: str | Path, *, key: str | None = None) -> np.ndarray:
    loaded = np.load(Path(path))
    if isinstance(loaded, np.lib.npyio.NpzFile):
        if key is None:
            keys = list(loaded.keys())
            if len(keys) != 1:
                raise ValueError(f"NPZ weight file {path} requires weights_key; found {keys}")
            key = keys[0]
        return np.asarray(loaded[key], dtype=np.int32)
    return np.asarray(loaded, dtype=np.int32)


def _unbalanced_conv_weights(
    kh: int,
    kw: int,
    in_channels: int,
    out_channels: int,
    sparsity: float,
    rng: np.random.Generator,
    *,
    max_weight: int,
    crossbar_size: int,
) -> np.ndarray:
    weights = np.zeros((kh, kw, in_channels, out_channels), dtype=np.int32)
    row_blocks = max(1, int(np.ceil(in_channels / crossbar_size)))
    col_blocks = max(1, int(np.ceil(out_channels / crossbar_size)))

    for i in range(kh):
        for j in range(kw):
            matrix_rank = i * kw + j
            matrix_bias = ((matrix_rank % 5) - 2) * 0.08
            for rb in range(row_blocks):
                for cb in range(col_blocks):
                    block_bias = ((rb * 3 + cb * 5 + matrix_rank) % 7 - 3) * 0.055
                    local_sparsity = float(np.clip(sparsity + matrix_bias + block_bias, 0.05, 0.96))
                    r0 = rb * crossbar_size
                    r1 = min(in_channels, r0 + crossbar_size)
                    c0 = cb * crossbar_size
                    c1 = min(out_channels, c0 + crossbar_size)
                    values = rng.integers(1, max_weight + 1, size=(r1 - r0, c1 - c0), dtype=np.int32)
                    weights[i, j, r0:r1, c0:c1] = _apply_sparsity(values, local_sparsity, rng)
    return weights


def build_workload(config: dict[str, Any], *, seed: int, crossbar_size: int) -> Workload:
    rng = np.random.default_rng(seed)
    layers: list[LayerSpec] = []
    max_weight = int(config.get("max_weight", 15))

    if "model_zoo" in config:
        return build_model_zoo_workload(
            config["model_zoo"],
            seed=seed,
            crossbar_size=crossbar_size,
            max_weight=max_weight,
        )

    for layer_config in config.get("layers", []):
        layer_type = layer_config["type"]
        name = layer_config["name"]
        sparsity = float(layer_config.get("sparsity", 0.7))
        distribution = layer_config.get("distribution", "balanced")

        if layer_type == "conv2d":
            kh = int(layer_config["kernel_h"])
            kw = int(layer_config["kernel_w"])
            in_channels = int(layer_config["in_channels"])
            out_channels = int(layer_config["out_channels"])
            if "weights_path" in layer_config:
                weights = _load_weights(
                    layer_config["weights_path"],
                    key=layer_config.get("weights_key"),
                )
            elif distribution == "unbalanced":
                weights = _unbalanced_conv_weights(
                    kh,
                    kw,
                    in_channels,
                    out_channels,
                    sparsity,
                    rng,
                    max_weight=max_weight,
                    crossbar_size=crossbar_size,
                )
            else:
                weights = _balanced_weights(
                    (kh, kw, in_channels, out_channels),
                    sparsity,
                    rng,
                    max_weight=max_weight,
                )
            layers.append(
                LayerSpec(
                    name=name,
                    type=layer_type,
                    weights=weights,
                    input_h=int(layer_config["input_h"]),
                    input_w=int(layer_config["input_w"]),
                    stride=int(layer_config.get("stride", 1)),
                    padding=int(layer_config.get("padding", 0)),
                )
            )
        elif layer_type == "linear":
            rows = int(layer_config["in_features"])
            cols = int(layer_config["out_features"])
            if "weights_path" in layer_config:
                weights = _load_weights(
                    layer_config["weights_path"],
                    key=layer_config.get("weights_key"),
                )
            else:
                weights = _balanced_weights((rows, cols), sparsity, rng, max_weight=max_weight)
            layers.append(LayerSpec(name=name, type=layer_type, weights=weights))
        else:
            raise ValueError(f"Unsupported layer type: {layer_type}")

    return Workload(name=config.get("name", "workload"), layers=tuple(layers))


def _conv_layer(
    *,
    name: str,
    kh: int,
    kw: int,
    in_channels: int,
    out_channels: int,
    input_h: int,
    input_w: int,
    sparsity: float,
    distribution: str,
    rng: np.random.Generator,
    crossbar_size: int,
    max_weight: int,
    stride: int = 1,
    padding: int = 0,
) -> LayerSpec:
    if distribution == "unbalanced":
        weights = _unbalanced_conv_weights(
            kh,
            kw,
            in_channels,
            out_channels,
            sparsity,
            rng,
            max_weight=max_weight,
            crossbar_size=crossbar_size,
        )
    else:
        weights = _balanced_weights(
            (kh, kw, in_channels, out_channels),
            sparsity,
            rng,
            max_weight=max_weight,
        )
    return LayerSpec(
        name=name,
        type="conv2d",
        weights=weights,
        input_h=input_h,
        input_w=input_w,
        stride=stride,
        padding=padding,
        metadata={
            "in_channels": in_channels,
            "out_channels": out_channels,
            "kernel": f"{kh}x{kw}",
        },
    )


def build_model_zoo_workload(
    config: dict[str, Any],
    *,
    seed: int,
    crossbar_size: int,
    max_weight: int,
) -> Workload:
    family = str(config.get("family", "")).lower()
    dataset = str(config.get("dataset", "imagenet")).lower()
    sparsity = float(config.get("sparsity", 0.75))
    distribution = str(config.get("distribution", "unbalanced"))
    max_layers = config.get("max_layers")
    rng = np.random.default_rng(seed)

    if family == "vgg19":
        layers = _build_vgg19_layers(
            dataset=dataset,
            sparsity=sparsity,
            distribution=distribution,
            rng=rng,
            crossbar_size=crossbar_size,
            max_weight=max_weight,
        )
    elif family == "resnet50":
        layers = _build_resnet50_layers(
            dataset=dataset,
            sparsity=sparsity,
            distribution=distribution,
            rng=rng,
            crossbar_size=crossbar_size,
            max_weight=max_weight,
        )
    else:
        raise ValueError(f"Unsupported model_zoo family: {family}")

    if max_layers is not None:
        layers = layers[: int(max_layers)]
    name = f"{family}_{dataset}_{int(sparsity * 100)}pct_sparse"
    return Workload(name=name, layers=tuple(layers))


def _dataset_input_size(dataset: str) -> int:
    if dataset in {"cifar", "cifar100", "cifar-100"}:
        return 32
    return 224


def _build_vgg19_layers(
    *,
    dataset: str,
    sparsity: float,
    distribution: str,
    rng: np.random.Generator,
    crossbar_size: int,
    max_weight: int,
) -> list[LayerSpec]:
    channels: list[int | str] = [
        64,
        64,
        "M",
        128,
        128,
        "M",
        256,
        256,
        256,
        256,
        "M",
        512,
        512,
        512,
        512,
        "M",
        512,
        512,
        512,
        512,
        "M",
    ]
    h = w = _dataset_input_size(dataset)
    in_channels = 3
    conv_index = 1
    layers: list[LayerSpec] = []
    for entry in channels:
        if entry == "M":
            h = max(1, h // 2)
            w = max(1, w // 2)
            continue
        out_channels = int(entry)
        layers.append(
            _conv_layer(
                name=f"vgg19_conv{conv_index:02d}_{in_channels}x{out_channels}",
                kh=3,
                kw=3,
                in_channels=in_channels,
                out_channels=out_channels,
                input_h=h,
                input_w=w,
                sparsity=sparsity,
                distribution=distribution,
                rng=rng,
                crossbar_size=crossbar_size,
                max_weight=max_weight,
                padding=1,
            )
        )
        in_channels = out_channels
        conv_index += 1
    return layers


def _build_resnet50_layers(
    *,
    dataset: str,
    sparsity: float,
    distribution: str,
    rng: np.random.Generator,
    crossbar_size: int,
    max_weight: int,
) -> list[LayerSpec]:
    input_size = _dataset_input_size(dataset)
    layers: list[LayerSpec] = []
    layers.append(
        _conv_layer(
            name="resnet50_stem_7x7",
            kh=7,
            kw=7,
            in_channels=3,
            out_channels=64,
            input_h=input_size,
            input_w=input_size,
            sparsity=sparsity,
            distribution=distribution,
            rng=rng,
            crossbar_size=crossbar_size,
            max_weight=max_weight,
            stride=2 if input_size > 32 else 1,
            padding=3,
        )
    )
    h = w = input_size // 4 if input_size > 32 else input_size
    in_channels = 64
    stages = [(2, 64, 3, 1), (3, 128, 4, 2), (4, 256, 6, 2), (5, 512, 3, 2)]
    for stage_id, bottleneck, blocks, first_stride in stages:
        out_channels = bottleneck * 4
        for block_id in range(1, blocks + 1):
            stride = first_stride if block_id == 1 else 1
            prefix = f"resnet50_s{stage_id}_b{block_id}"
            layers.append(
                _conv_layer(
                    name=f"{prefix}_conv1_1x1",
                    kh=1,
                    kw=1,
                    in_channels=in_channels,
                    out_channels=bottleneck,
                    input_h=h,
                    input_w=w,
                    sparsity=sparsity,
                    distribution=distribution,
                    rng=rng,
                    crossbar_size=crossbar_size,
                    max_weight=max_weight,
                )
            )
            if stride > 1:
                conv2_input_h = h
                conv2_input_w = w
                h = max(1, h // stride)
                w = max(1, w // stride)
            else:
                conv2_input_h = h
                conv2_input_w = w
            layers.append(
                _conv_layer(
                    name=f"{prefix}_conv2_3x3",
                    kh=3,
                    kw=3,
                    in_channels=bottleneck,
                    out_channels=bottleneck,
                    input_h=conv2_input_h,
                    input_w=conv2_input_w,
                    sparsity=sparsity,
                    distribution=distribution,
                    rng=rng,
                    crossbar_size=crossbar_size,
                    max_weight=max_weight,
                    stride=stride,
                    padding=1,
                )
            )
            layers.append(
                _conv_layer(
                    name=f"{prefix}_conv3_1x1",
                    kh=1,
                    kw=1,
                    in_channels=bottleneck,
                    out_channels=out_channels,
                    input_h=h,
                    input_w=w,
                    sparsity=sparsity,
                    distribution=distribution,
                    rng=rng,
                    crossbar_size=crossbar_size,
                    max_weight=max_weight,
                )
            )
            if block_id == 1 or in_channels != out_channels:
                layers.append(
                    _conv_layer(
                        name=f"{prefix}_projection_1x1",
                        kh=1,
                        kw=1,
                        in_channels=in_channels,
                        out_channels=out_channels,
                        input_h=conv2_input_h if stride > 1 else h,
                        input_w=conv2_input_w if stride > 1 else w,
                        sparsity=sparsity,
                        distribution=distribution,
                        rng=rng,
                        crossbar_size=crossbar_size,
                        max_weight=max_weight,
                        stride=stride,
                    )
                )
            in_channels = out_channels
    return layers
