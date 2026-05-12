"""SAMBA load-balancing passes."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import count

import numpy as np

from samba.architecture import HardwareConfig, OptimizationConfig
from samba.mapping import MVMUBlock


@dataclass
class BalanceStats:
    column_swaps: int = 0
    row_swaps: int = 0
    split_mvmus: int = 0
    skipped_splits: int = 0
    guarded_layers: int = 0

    @property
    def rearrange_vectors(self) -> int:
        # Each exchange pair needs two vector rearranges to rebuild both operands.
        return 2 * (self.column_swaps + self.row_swaps)

    def as_dict(self) -> dict[str, int]:
        return {
            "column_swaps": self.column_swaps,
            "row_swaps": self.row_swaps,
            "split_mvmus": self.split_mvmus,
            "skipped_splits": self.skipped_splits,
            "guarded_layers": self.guarded_layers,
            "rearrange_vectors": self.rearrange_vectors,
        }


_SPLIT_IDS = count(1_000_000)


def _latency(block: MVMUBlock, hw: HardwareConfig) -> float:
    return block.estimate(hw, reconfigurable_adc=True).latency_cycles


def _column_costs(block: MVMUBlock, hw: HardwareConfig) -> np.ndarray:
    return block.estimate(hw, reconfigurable_adc=True).column_cost_cycles


def _row_scores(block: MVMUBlock) -> np.ndarray:
    return np.count_nonzero(block.weights, axis=1).astype(np.float64)


def _group_by(blocks: list[MVMUBlock], key: str) -> dict[tuple[int, int], list[MVMUBlock]]:
    grouped: dict[tuple[int, int], list[MVMUBlock]] = defaultdict(list)
    for block in blocks:
        if key == "matrix_row":
            grouped[(block.matrix_id, block.row_block)].append(block)
        elif key == "matrix":
            grouped[(block.matrix_id, -1)].append(block)
        else:
            raise ValueError(f"Unknown group key {key}")
    return grouped


def apply_column_exchange(
    blocks: list[MVMUBlock],
    hw: HardwareConfig,
    opt: OptimizationConfig,
) -> BalanceStats:
    """Balance MVMUs that share an input vector by swapping expensive columns."""

    stats = BalanceStats()
    if not opt.enable_column_exchange:
        return stats

    for group in _group_by(blocks, "matrix_row").values():
        if len(group) < 2:
            continue
        for _ in range(opt.max_column_exchange_iters):
            ranked = sorted(group, key=lambda block: _latency(block, hw))
            fast = ranked[0]
            slow = ranked[-1]
            old_fast = _latency(fast, hw)
            old_slow = _latency(slow, hw)
            if old_slow <= 0:
                break
            if (old_slow - old_fast) / old_slow < opt.balance_gap_ratio:
                break

            slow_costs = _column_costs(slow, hw)
            fast_costs = _column_costs(fast, hw)
            slow_col = int(np.argmax(slow_costs))
            fast_col = int(np.argmin(fast_costs))
            if slow_costs[slow_col] <= fast_costs[fast_col]:
                break

            slow_candidate = slow.weights.copy()
            fast_candidate = fast.weights.copy()
            slow_candidate[:, slow_col], fast_candidate[:, fast_col] = (
                fast.weights[:, fast_col].copy(),
                slow.weights[:, slow_col].copy(),
            )
            slow.weights = slow_candidate
            fast.weights = fast_candidate
            new_max = max(_latency(fast, hw), _latency(slow, hw))
            old_max = max(old_fast, old_slow)

            if old_max - new_max >= opt.min_improvement_cycles:
                pair = tuple(sorted((fast.id, slow.id)))
                fast.column_rearrange_pairs.add(pair)
                slow.column_rearrange_pairs.add(pair)
                stats.column_swaps += 1
            else:
                slow.weights = slow_candidate.copy()
                fast.weights = fast_candidate.copy()
                slow.weights[:, slow_col], fast.weights[:, fast_col] = (
                    fast_candidate[:, fast_col].copy(),
                    slow_candidate[:, slow_col].copy(),
                )
                break
    return stats


def apply_row_exchange(
    blocks: list[MVMUBlock],
    hw: HardwareConfig,
    opt: OptimizationConfig,
) -> BalanceStats:
    """Balance row-block MVMU groups by swapping whole logical input rows."""

    stats = BalanceStats()
    if not opt.enable_row_exchange:
        return stats

    for matrix_group in _group_by(blocks, "matrix").values():
        by_row: dict[int, list[MVMUBlock]] = defaultdict(list)
        for block in matrix_group:
            by_row[block.row_block].append(block)
        if len(by_row) < 2:
            continue

        for _ in range(opt.max_row_exchange_iters):
            row_latency = {
                row_block: max(_latency(block, hw) for block in row_blocks)
                for row_block, row_blocks in by_row.items()
            }
            fast_row = min(row_latency, key=row_latency.get)
            slow_row = max(row_latency, key=row_latency.get)
            old_fast = row_latency[fast_row]
            old_slow = row_latency[slow_row]
            if old_slow <= 0:
                break
            if (old_slow - old_fast) / old_slow < opt.balance_gap_ratio:
                break

            slow_blocks = sorted(by_row[slow_row], key=lambda block: block.col_block)
            fast_blocks = sorted(by_row[fast_row], key=lambda block: block.col_block)
            slow_scores = sum((_row_scores(block) for block in slow_blocks), start=np.zeros(hw.crossbar_size))
            fast_scores = sum((_row_scores(block) for block in fast_blocks), start=np.zeros(hw.crossbar_size))
            slow_idx = int(np.argmax(slow_scores))
            fast_idx = int(np.argmin(fast_scores))
            if slow_scores[slow_idx] <= fast_scores[fast_idx]:
                break

            snapshots = [(block, block.weights.copy()) for block in slow_blocks + fast_blocks]
            for slow_block, fast_block in zip(slow_blocks, fast_blocks):
                slow_row_values = slow_block.weights[slow_idx, :].copy()
                fast_row_values = fast_block.weights[fast_idx, :].copy()
                slow_block.weights[slow_idx, :] = fast_row_values
                fast_block.weights[fast_idx, :] = slow_row_values

            new_slow = max(_latency(block, hw) for block in slow_blocks)
            new_fast = max(_latency(block, hw) for block in fast_blocks)
            if max(old_slow, old_fast) - max(new_slow, new_fast) >= opt.min_improvement_cycles:
                for slow_block, fast_block in zip(slow_blocks, fast_blocks):
                    pair = tuple(sorted((slow_block.id, fast_block.id)))
                    slow_block.row_rearrange_pairs.add(pair)
                    fast_block.row_rearrange_pairs.add(pair)
                stats.row_swaps += 1
            else:
                for block, snapshot in snapshots:
                    block.weights = snapshot
                break
    return stats


def _split_candidate(block: MVMUBlock, hw: HardwareConfig) -> tuple[np.ndarray, np.ndarray]:
    costs = _column_costs(block, hw)
    left = np.zeros_like(block.weights)
    right = np.zeros_like(block.weights)
    left_cost = 0.0
    right_cost = 0.0
    for col in np.argsort(costs)[::-1]:
        col = int(col)
        if left_cost <= right_cost:
            left[:, col] = block.weights[:, col]
            left_cost += float(costs[col])
        else:
            right[:, col] = block.weights[:, col]
            right_cost += float(costs[col])
    return left, right


def apply_split_mvmus(
    blocks: list[MVMUBlock],
    hw: HardwareConfig,
    opt: OptimizationConfig,
) -> tuple[list[MVMUBlock], BalanceStats]:
    """Split slow MVMUs column-wise into two parallel MVMUs."""

    stats = BalanceStats()
    if not opt.enable_split or not blocks:
        return blocks, stats

    budget = int(max(0, round(len(blocks) * opt.split_extra_mvmu_fraction)))
    if budget == 0:
        return blocks, stats

    result = list(blocks)
    for block in sorted(blocks, key=lambda item: _latency(item, hw), reverse=True):
        if stats.split_mvmus >= budget:
            break
        old_latency = _latency(block, hw)
        left_weights, right_weights = _split_candidate(block, hw)
        if not np.any(left_weights) or not np.any(right_weights):
            stats.skipped_splits += 1
            continue

        left_latency = block.estimate(hw, reconfigurable_adc=True).latency_cycles
        block.weights = left_weights
        new_left = _latency(block, hw)
        child = MVMUBlock(
            layer_name=block.layer_name,
            matrix_id=block.matrix_id,
            row_block=block.row_block,
            col_block=block.col_block,
            weights=right_weights,
            original_shape=block.original_shape,
            id=next(_SPLIT_IDS),
            split_parent_id=block.logical_id,
            split_group_size=2,
        )
        block.split_parent_id = block.logical_id
        block.split_group_size = 2
        new_latency = max(new_left, _latency(child, hw)) + hw.alu_cycles

        if old_latency - new_latency >= opt.min_improvement_cycles:
            result.append(child)
            stats.split_mvmus += 1
        else:
            block.weights = left_weights + right_weights
            block.split_parent_id = None
            block.split_group_size = 1
            stats.skipped_splits += 1
        _ = left_latency

    return result, stats


def apply_load_balancing(
    blocks: list[MVMUBlock],
    hw: HardwareConfig,
    opt: OptimizationConfig,
) -> tuple[list[MVMUBlock], BalanceStats]:
    total = BalanceStats()
    col = apply_column_exchange(blocks, hw, opt)
    total.column_swaps += col.column_swaps
    row = apply_row_exchange(blocks, hw, opt)
    total.row_swaps += row.row_swaps
    blocks, split = apply_split_mvmus(blocks, hw, opt)
    total.split_mvmus += split.split_mvmus
    total.skipped_splits += split.skipped_splits
    return blocks, total
