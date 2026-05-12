"""Configuration models for the SAMBA simulator."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from math import ceil, log2
from typing import Any


def _with_defaults(cls: type, values: dict[str, Any] | None):
    values = values or {}
    allowed = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    unknown = sorted(set(values) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"Unknown {cls.__name__} option(s): {joined}")
    return cls(**values)


@dataclass(frozen=True)
class HardwareConfig:
    """Analog IMC hardware parameters.

    The defaults mirror the paper's illustrative PUMA-like setup. Timing and
    energy constants are intentionally explicit so the simulator can be
    calibrated without changing algorithm code.
    """

    crossbar_size: int = 64
    weight_bits: int = 16
    bits_per_slice: int = 2
    input_bits: int = 16
    input_stream_bits: int = 1
    mvmus_per_core: int = 4
    cores_per_tile: int = 4

    adc_cycle_per_bit: float = 1.0
    adc_energy_pj_per_bit: float = 0.85
    shift_add_cycles: float = 4.0
    shift_add_energy_pj: float = 6.0

    rearrange_cycles_per_vector: float = 12.0
    rearrange_energy_pj_per_vector: float = 18.0
    load_cycles: float = 18.0
    store_cycles: float = 18.0
    send_cycles: float = 32.0
    receive_cycles: float = 32.0
    alu_cycles: float = 4.0
    movement_energy_pj: float = 25.0

    @classmethod
    def from_dict(cls, values: dict[str, Any] | None) -> "HardwareConfig":
        return _with_defaults(cls, values)

    def validate(self) -> None:
        positive_ints = [
            "crossbar_size",
            "weight_bits",
            "bits_per_slice",
            "input_bits",
            "input_stream_bits",
            "mvmus_per_core",
            "cores_per_tile",
        ]
        for name in positive_ints:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.bits_per_slice > self.weight_bits:
            raise ValueError("bits_per_slice cannot exceed weight_bits")

    @property
    def weight_slices(self) -> int:
        return ceil(self.weight_bits / self.bits_per_slice)

    @property
    def input_streams(self) -> int:
        return ceil(self.input_bits / self.input_stream_bits)

    @property
    def full_precision_adc_bits(self) -> int:
        return ceil(log2(self.crossbar_size)) + self.bits_per_slice + self.input_stream_bits - 1

    @property
    def tile_capacity(self) -> int:
        return self.cores_per_tile * self.mvmus_per_core

    def adc_latency(self, bits: int | float) -> float:
        return max(0.0, float(bits)) * self.adc_cycle_per_bit

    def adc_energy(self, bits: int | float) -> float:
        return max(0.0, float(bits)) * self.adc_energy_pj_per_bit


@dataclass(frozen=True)
class OptimizationConfig:
    """SAMBA compiler/scheduler optimization switches and heuristics."""

    enable_column_exchange: bool = True
    enable_row_exchange: bool = True
    enable_split: bool = True
    enable_optimized_allocation: bool = True
    enable_tree_reduction: bool = True
    enable_latency_sort: bool = True
    enable_input_prefetch: bool = True
    enable_profit_guard: bool = True

    max_column_exchange_iters: int = 128
    max_row_exchange_iters: int = 64
    min_improvement_cycles: float = 1.0
    balance_gap_ratio: float = 0.08
    split_extra_mvmu_fraction: float = 0.2
    input_prefetch_depth: int = 2

    @classmethod
    def from_dict(cls, values: dict[str, Any] | None) -> "OptimizationConfig":
        return _with_defaults(cls, values)

    def with_overrides(self, **values: Any) -> "OptimizationConfig":
        return replace(self, **values)

    def disabled_for_baseline(self) -> "OptimizationConfig":
        return replace(
            self,
            enable_column_exchange=False,
            enable_row_exchange=False,
            enable_split=False,
            enable_optimized_allocation=False,
            enable_tree_reduction=False,
            enable_latency_sort=False,
            enable_input_prefetch=False,
            enable_profit_guard=False,
        )


@dataclass(frozen=True)
class SimulationConfig:
    """Top-level experiment configuration."""

    seed: int = 7
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    optimizations: OptimizationConfig = field(default_factory=OptimizationConfig)
    workload: dict[str, Any] = field(default_factory=dict)
    variants: tuple[dict[str, Any], ...] = ()
    variant_suite: str = "default"
    trace_limit: int = 1_000

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "SimulationConfig":
        hardware = HardwareConfig.from_dict(values.get("hardware"))
        hardware.validate()
        optimizations = OptimizationConfig.from_dict(values.get("optimizations"))
        return cls(
            seed=int(values.get("seed", 7)),
            hardware=hardware,
            optimizations=optimizations,
            workload=values.get("workload", {}),
            variants=tuple(values.get("variants", ())),
            variant_suite=str(values.get("variant_suite", "default")),
            trace_limit=int(values.get("trace_limit", 1_000)),
        )
