"""ADC precision and cost model."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2

import numpy as np

from samba.architecture import HardwareConfig


@dataclass(frozen=True)
class MVMUEstimate:
    latency_cycles: float
    energy_pj: float
    adc_precision_bits: np.ndarray
    column_cost_cycles: np.ndarray

    @property
    def active_columns(self) -> int:
        return int(np.count_nonzero(np.any(self.adc_precision_bits > 0, axis=0)))

    @property
    def max_precision_bits(self) -> int:
        if self.adc_precision_bits.size == 0:
            return 0
        return int(np.max(self.adc_precision_bits))


def bit_slices(weights: np.ndarray, hw: HardwareConfig) -> list[np.ndarray]:
    """Return unsigned low-to-high bit slices for absolute fixed-point weights."""

    values = np.abs(weights.astype(np.int64, copy=False))
    mask = (1 << hw.bits_per_slice) - 1
    slices: list[np.ndarray] = []
    for shift in range(0, hw.weight_bits, hw.bits_per_slice):
        slices.append((values >> shift) & mask)
    return slices


def required_adc_precision(sum_value: int, hw: HardwareConfig) -> int:
    """Precision from the paper's ceil(log2(sum_i vmax*w_ij)) + 1 rule."""

    if sum_value <= 0:
        return 0
    precision = int(ceil(log2(sum_value))) + 1
    return min(precision, hw.full_precision_adc_bits)


def column_precisions(weights: np.ndarray, hw: HardwareConfig) -> np.ndarray:
    """Estimate ADC bits for each bit-slice crossbar column."""

    vmax = max(1, (1 << hw.input_stream_bits) - 1)
    per_slice: list[np.ndarray] = []
    for weight_slice in bit_slices(weights, hw):
        column_sums = np.sum(weight_slice, axis=0, dtype=np.int64) * vmax
        precisions = np.array(
            [required_adc_precision(int(total), hw) for total in column_sums],
            dtype=np.int16,
        )
        per_slice.append(precisions)
    return np.vstack(per_slice)


def estimate_mvmu(
    weights: np.ndarray,
    hw: HardwareConfig,
    *,
    reconfigurable_adc: bool,
) -> MVMUEstimate:
    """Estimate one MVMU's MVM latency and energy.

    One ADC is modeled per bit-slice crossbar. Columns are serialized within a
    crossbar; bit-slice crossbars run in parallel, so the slowest slice controls
    ADC latency for each input bit stream.
    """

    if reconfigurable_adc:
        precisions = column_precisions(weights, hw)
    else:
        active = np.ones((hw.weight_slices, weights.shape[1]), dtype=np.int16)
        precisions = active * hw.full_precision_adc_bits

    per_column_cycles = np.vectorize(hw.adc_latency)(precisions).sum(axis=0)
    per_slice_cycles = np.vectorize(hw.adc_latency)(precisions).sum(axis=1)
    adc_cycles = hw.input_streams * float(np.max(per_slice_cycles, initial=0.0))
    latency = adc_cycles + hw.shift_add_cycles

    adc_energy = float(np.vectorize(hw.adc_energy)(precisions).sum()) * hw.input_streams
    active_slices = int(np.count_nonzero(np.any(precisions > 0, axis=1)))
    energy = adc_energy + active_slices * hw.shift_add_energy_pj
    return MVMUEstimate(
        latency_cycles=latency,
        energy_pj=energy,
        adc_precision_bits=precisions,
        column_cost_cycles=per_column_cycles,
    )
