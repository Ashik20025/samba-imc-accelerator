"""MVMU allocation across cores and tiles."""

from __future__ import annotations

from dataclasses import dataclass, field

from samba.architecture import HardwareConfig, OptimizationConfig
from samba.mapping import MVMUBlock


@dataclass
class CorePlan:
    core_id: int
    tile_id: int
    blocks: list[MVMUBlock] = field(default_factory=list)

    def append(self, block: MVMUBlock) -> None:
        self.blocks.append(block)


@dataclass(frozen=True)
class AllocationPlan:
    cores: tuple[CorePlan, ...]

    @property
    def core_count(self) -> int:
        return len(self.cores)

    @property
    def tile_count(self) -> int:
        return len({core.tile_id for core in self.cores})


def _baseline_key(block: MVMUBlock) -> tuple[int, int, int, int]:
    return (block.matrix_id, block.row_block, block.col_block, block.id)


def _optimized_key(block: MVMUBlock) -> tuple[int, int, int, int, int]:
    has_rearrange = int(bool(block.column_rearrange_pairs or block.row_rearrange_pairs))
    return (
        block.matrix_id,
        -has_rearrange,
        block.row_block,
        block.col_block,
        block.logical_id,
    )


def allocate_blocks(
    blocks: list[MVMUBlock],
    hw: HardwareConfig,
    opt: OptimizationConfig,
) -> AllocationPlan:
    """Pack MVMUs into cores.

    SAMBA-aware allocation prioritizes MVMUs involved in rearrangement and then
    groups shared matrix/column blocks, which reduces shared-memory traffic for
    output rearrange and column-wise accumulation.
    """

    key = _optimized_key if opt.enable_optimized_allocation else _baseline_key
    ordered = sorted(blocks, key=key)
    cores: list[CorePlan] = []
    current: CorePlan | None = None
    for block in ordered:
        if current is None or len(current.blocks) >= hw.mvmus_per_core:
            core_id = len(cores)
            current = CorePlan(core_id=core_id, tile_id=core_id // hw.cores_per_tile)
            cores.append(current)
        current.append(block)
    return AllocationPlan(cores=tuple(cores))
