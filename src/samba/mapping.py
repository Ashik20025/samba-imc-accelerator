"""Weight mapping into crossbar MVMU blocks."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count

import numpy as np

from samba.adc import MVMUEstimate, estimate_mvmu
from samba.architecture import HardwareConfig
from samba.workload import LayerSpec


_BLOCK_IDS = count()


@dataclass
class MVMUBlock:
    layer_name: str
    matrix_id: int
    row_block: int
    col_block: int
    weights: np.ndarray
    original_shape: tuple[int, int]
    id: int = field(default_factory=lambda: next(_BLOCK_IDS))
    split_parent_id: int | None = None
    split_group_size: int = 1
    column_rearrange_pairs: set[tuple[int, int]] = field(default_factory=set)
    row_rearrange_pairs: set[tuple[int, int]] = field(default_factory=set)

    def clone(self) -> "MVMUBlock":
        return MVMUBlock(
            layer_name=self.layer_name,
            matrix_id=self.matrix_id,
            row_block=self.row_block,
            col_block=self.col_block,
            weights=self.weights.copy(),
            original_shape=self.original_shape,
            id=self.id,
            split_parent_id=self.split_parent_id,
            split_group_size=self.split_group_size,
            column_rearrange_pairs=set(self.column_rearrange_pairs),
            row_rearrange_pairs=set(self.row_rearrange_pairs),
        )

    @property
    def logical_id(self) -> int:
        return self.split_parent_id if self.split_parent_id is not None else self.id

    def estimate(self, hw: HardwareConfig, *, reconfigurable_adc: bool) -> MVMUEstimate:
        return estimate_mvmu(self.weights, hw, reconfigurable_adc=reconfigurable_adc)


@dataclass(frozen=True)
class MappedLayer:
    layer: LayerSpec
    blocks: tuple[MVMUBlock, ...]

    @property
    def windows(self) -> int:
        return self.layer.windows

    def clone_blocks(self) -> list[MVMUBlock]:
        return [block.clone() for block in self.blocks]


def _pad_matrix(matrix: np.ndarray, rows: int, cols: int) -> np.ndarray:
    padded = np.zeros((rows, cols), dtype=np.int32)
    padded[: matrix.shape[0], : matrix.shape[1]] = matrix
    return padded


def _partition_matrix(
    *,
    layer_name: str,
    matrix_id: int,
    matrix: np.ndarray,
    hw: HardwareConfig,
) -> list[MVMUBlock]:
    blocks: list[MVMUBlock] = []
    rows, cols = matrix.shape
    for row_start in range(0, rows, hw.crossbar_size):
        for col_start in range(0, cols, hw.crossbar_size):
            submatrix = matrix[
                row_start : min(row_start + hw.crossbar_size, rows),
                col_start : min(col_start + hw.crossbar_size, cols),
            ]
            blocks.append(
                MVMUBlock(
                    layer_name=layer_name,
                    matrix_id=matrix_id,
                    row_block=row_start // hw.crossbar_size,
                    col_block=col_start // hw.crossbar_size,
                    weights=_pad_matrix(submatrix, hw.crossbar_size, hw.crossbar_size),
                    original_shape=submatrix.shape,
                )
            )
    return blocks


def map_layer(layer: LayerSpec, hw: HardwareConfig) -> MappedLayer:
    blocks: list[MVMUBlock] = []
    if layer.is_conv:
        kh, kw = layer.weights.shape[:2]
        matrix_id = 0
        for i in range(kh):
            for j in range(kw):
                matrix = layer.weights[i, j, :, :]
                blocks.extend(
                    _partition_matrix(
                        layer_name=layer.name,
                        matrix_id=matrix_id,
                        matrix=matrix,
                        hw=hw,
                    )
                )
                matrix_id += 1
    else:
        blocks.extend(
            _partition_matrix(layer_name=layer.name, matrix_id=0, matrix=layer.weights, hw=hw)
        )
    return MappedLayer(layer=layer, blocks=tuple(blocks))
