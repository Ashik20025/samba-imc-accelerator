"""Experiment orchestration and timing simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Iterable

from samba.allocator import AllocationPlan, CorePlan, allocate_blocks
from samba.architecture import HardwareConfig, OptimizationConfig, SimulationConfig
from samba.balancing import BalanceStats, apply_load_balancing
from samba.mapping import MappedLayer, MVMUBlock, map_layer
from samba.workload import Workload, build_workload


@dataclass(frozen=True)
class CoreRuntime:
    core_id: int
    tile_id: int
    latency_cycles: float
    energy_pj: float


@dataclass(frozen=True)
class TraceEvent:
    layer: str
    variant: str
    op: str
    start_cycle: float
    end_cycle: float
    core_id: int | None = None
    tile_id: int | None = None
    detail: str = ""


@dataclass(frozen=True)
class LayerMetrics:
    layer: str
    variant: str
    windows: int
    blocks: int
    cores: int
    tiles: int
    latency_cycles: float
    energy_pj: float
    speedup_vs_fixed_adc: float
    energy_efficiency_vs_fixed_adc: float
    balance: dict[str, int]
    avg_core_latency_cycles: float = 0.0
    bottleneck_core_cycles: float = 0.0
    movement_cycles: float = 0.0
    utilization: float = 0.0
    rearrange_vectors: int = 0


@dataclass(frozen=True)
class VariantSummary:
    variant: str
    latency_cycles: float
    energy_pj: float
    speedup_vs_fixed_adc: float
    energy_efficiency_vs_fixed_adc: float


@dataclass(frozen=True)
class VariantPlan:
    name: str
    reconfigurable_adc: bool
    apply_balancing: bool
    optimizations: OptimizationConfig


@dataclass(frozen=True)
class ExperimentResult:
    workload: str
    hardware: dict[str, object]
    variants: tuple[VariantSummary, ...]
    layers: tuple[LayerMetrics, ...]
    traces: tuple[TraceEvent, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "workload": self.workload,
            "hardware": self.hardware,
            "variants": [asdict(item) for item in self.variants],
            "layers": [asdict(item) for item in self.layers],
            "traces": [asdict(item) for item in self.traces],
        }


def _unique_rearrange_vectors(blocks: Iterable[MVMUBlock]) -> int:
    pairs: set[tuple[int, int]] = set()
    for block in blocks:
        pairs.update(block.column_rearrange_pairs)
        pairs.update(block.row_rearrange_pairs)
    return 2 * len(pairs)


def _core_runtime(
    core: CorePlan,
    hw: HardwareConfig,
    *,
    reconfigurable_adc: bool,
) -> CoreRuntime:
    estimates = [block.estimate(hw, reconfigurable_adc=reconfigurable_adc) for block in core.blocks]
    latency = max((estimate.latency_cycles for estimate in estimates), default=0.0)
    energy = sum(estimate.energy_pj for estimate in estimates)
    return CoreRuntime(
        core_id=core.core_id,
        tile_id=core.tile_id,
        latency_cycles=latency,
        energy_pj=energy,
    )


def _transfer_cycles(left: CoreRuntime, right: CoreRuntime, hw: HardwareConfig) -> float:
    cycles = hw.load_cycles + hw.store_cycles
    if left.tile_id != right.tile_id:
        cycles += hw.send_cycles + hw.receive_cycles
    return cycles


def _transfer_energy(left: CoreRuntime, right: CoreRuntime, hw: HardwareConfig) -> float:
    hops = 2 if left.tile_id == right.tile_id else 4
    return hops * hw.movement_energy_pj


def _linear_reduce(cores: list[CoreRuntime], hw: HardwareConfig) -> tuple[float, float]:
    if not cores:
        return 0.0, 0.0
    current = cores[0]
    ready = current.latency_cycles
    energy = 0.0
    for next_core in cores[1:]:
        ready = max(ready + _transfer_cycles(current, next_core, hw), next_core.latency_cycles)
        ready += hw.alu_cycles
        energy += _transfer_energy(current, next_core, hw) + hw.shift_add_energy_pj
        current = CoreRuntime(next_core.core_id, next_core.tile_id, ready, current.energy_pj)
    return ready, energy


def _tree_reduce(
    cores: list[CoreRuntime],
    hw: HardwareConfig,
    *,
    latency_sort: bool,
) -> tuple[float, float]:
    if not cores:
        return 0.0, 0.0
    active = sorted(cores, key=lambda item: item.latency_cycles) if latency_sort else list(cores)
    energy = 0.0
    while len(active) > 1:
        next_level: list[CoreRuntime] = []
        for index in range(0, len(active), 2):
            if index + 1 >= len(active):
                next_level.append(active[index])
                continue
            left = active[index]
            right = active[index + 1]
            transfer = _transfer_cycles(left, right, hw)
            ready = max(left.latency_cycles + transfer, right.latency_cycles) + hw.alu_cycles
            energy += _transfer_energy(left, right, hw) + hw.shift_add_energy_pj
            receiver = right if right.latency_cycles >= left.latency_cycles else left
            next_level.append(
                CoreRuntime(
                    core_id=receiver.core_id,
                    tile_id=receiver.tile_id,
                    latency_cycles=ready,
                    energy_pj=left.energy_pj + right.energy_pj,
                )
            )
        active = sorted(next_level, key=lambda item: item.latency_cycles) if latency_sort else next_level
    return active[0].latency_cycles, energy


def _simulate_with_blocks(
    mapped: MappedLayer,
    blocks: list[MVMUBlock],
    hw: HardwareConfig,
    opt: OptimizationConfig,
    *,
    variant: str,
    reconfigurable_adc: bool,
    balance: BalanceStats,
) -> tuple[LayerMetrics, float, float, list[TraceEvent]]:
    allocation = allocate_blocks(blocks, hw, opt)
    core_runtimes = [
        _core_runtime(core, hw, reconfigurable_adc=reconfigurable_adc) for core in allocation.cores
    ]
    trace_events = [
        TraceEvent(
            layer=mapped.layer.name,
            variant=variant,
            op="MVM",
            start_cycle=0.0,
            end_cycle=core.latency_cycles,
            core_id=core.core_id,
            tile_id=core.tile_id,
            detail=f"{len(allocation.cores[core.core_id].blocks)} mapped MVMU block(s)",
        )
        for core in core_runtimes
    ]

    if opt.enable_tree_reduction:
        reduction_latency, movement_energy = _tree_reduce(
            core_runtimes,
            hw,
            latency_sort=opt.enable_latency_sort,
        )
    else:
        reduction_latency, movement_energy = _linear_reduce(core_runtimes, hw)

    rearrange_vectors = _unique_rearrange_vectors(blocks)
    rearrange_cycles = rearrange_vectors * hw.rearrange_cycles_per_vector
    rearrange_energy = rearrange_vectors * hw.rearrange_energy_pj_per_vector
    split_cycles = balance.split_mvmus * hw.alu_cycles
    split_energy = balance.split_mvmus * hw.shift_add_energy_pj
    bottleneck_core = max((core.latency_cycles for core in core_runtimes), default=0.0)
    avg_core_latency = (
        sum(core.latency_cycles for core in core_runtimes) / len(core_runtimes)
        if core_runtimes
        else 0.0
    )
    utilization = (
        sum(core.latency_cycles for core in core_runtimes) / (len(core_runtimes) * bottleneck_core)
        if core_runtimes and bottleneck_core > 0
        else 0.0
    )
    movement_cycles = max(0.0, reduction_latency - bottleneck_core)
    trace_events.append(
        TraceEvent(
            layer=mapped.layer.name,
            variant=variant,
            op="TREE_REDUCE" if opt.enable_tree_reduction else "CHAIN_REDUCE",
            start_cycle=bottleneck_core,
            end_cycle=reduction_latency,
            detail=f"{allocation.core_count} core(s), {allocation.tile_count} tile(s)",
        )
    )
    if rearrange_cycles:
        trace_events.append(
            TraceEvent(
                layer=mapped.layer.name,
                variant=variant,
                op="REARRANGE",
                start_cycle=reduction_latency,
                end_cycle=reduction_latency + rearrange_cycles,
                detail=f"{rearrange_vectors} vector rearrange(s)",
            )
        )
    if split_cycles:
        trace_events.append(
            TraceEvent(
                layer=mapped.layer.name,
                variant=variant,
                op="SPLIT_MERGE",
                start_cycle=reduction_latency + rearrange_cycles,
                end_cycle=reduction_latency + rearrange_cycles + split_cycles,
                detail=f"{balance.split_mvmus} split MVMU merge(s)",
            )
        )

    per_window_latency = reduction_latency + rearrange_cycles + split_cycles
    per_window_energy = (
        sum(core.energy_pj for core in core_runtimes)
        + movement_energy
        + rearrange_energy
        + split_energy
    )
    windows = mapped.windows
    input_update_latency = 0.0
    if mapped.layer.is_conv and windows > 1:
        if opt.enable_input_prefetch:
            depth = max(1, opt.input_prefetch_depth)
            input_update_latency = (windows - 1) * hw.receive_cycles * 0.15 / depth
        else:
            input_update_latency = (windows - 1) * hw.receive_cycles

    latency = per_window_latency * windows + input_update_latency
    energy = per_window_energy * windows
    metrics = LayerMetrics(
        layer=mapped.layer.name,
        variant=variant,
        windows=windows,
        blocks=len(blocks),
        cores=allocation.core_count,
        tiles=allocation.tile_count,
        latency_cycles=latency,
        energy_pj=energy,
        speedup_vs_fixed_adc=1.0,
        energy_efficiency_vs_fixed_adc=1.0,
        balance=balance.as_dict(),
        avg_core_latency_cycles=avg_core_latency,
        bottleneck_core_cycles=bottleneck_core,
        movement_cycles=movement_cycles,
        utilization=utilization,
        rearrange_vectors=rearrange_vectors,
    )
    return metrics, latency, energy, trace_events


def _simulate_variant(
    mapped_layers: list[MappedLayer],
    hw: HardwareConfig,
    *,
    plan: VariantPlan,
) -> tuple[list[LayerMetrics], float, float, list[TraceEvent]]:
    layers: list[LayerMetrics] = []
    total_latency = 0.0
    total_energy = 0.0
    traces: list[TraceEvent] = []
    for mapped in mapped_layers:
        original_blocks = mapped.clone_blocks()
        layer_opt = plan.optimizations
        if plan.apply_balancing:
            candidate_blocks, candidate_balance = apply_load_balancing(
                [block.clone() for block in original_blocks],
                hw,
                layer_opt,
            )
            if layer_opt.enable_profit_guard:
                base_metrics, base_latency, base_energy, base_traces = _simulate_with_blocks(
                    mapped,
                    [block.clone() for block in original_blocks],
                    hw,
                    layer_opt,
                    variant=plan.name,
                    reconfigurable_adc=plan.reconfigurable_adc,
                    balance=BalanceStats(),
                )
                cand_metrics, cand_latency, cand_energy, cand_traces = _simulate_with_blocks(
                    mapped,
                    candidate_blocks,
                    hw,
                    layer_opt,
                    variant=plan.name,
                    reconfigurable_adc=plan.reconfigurable_adc,
                    balance=candidate_balance,
                )
                if cand_latency <= base_latency:
                    metrics, latency, energy, trace_events = (
                        cand_metrics,
                        cand_latency,
                        cand_energy,
                        cand_traces,
                    )
                else:
                    guarded = BalanceStats(guarded_layers=1)
                    metrics = replace(base_metrics, balance=guarded.as_dict())
                    latency, energy, trace_events = base_latency, base_energy, base_traces
            else:
                metrics, latency, energy, trace_events = _simulate_with_blocks(
                    mapped,
                    candidate_blocks,
                    hw,
                    layer_opt,
                    variant=plan.name,
                    reconfigurable_adc=plan.reconfigurable_adc,
                    balance=candidate_balance,
                )
        else:
            metrics, latency, energy, trace_events = _simulate_with_blocks(
                mapped,
                original_blocks,
                hw,
                layer_opt,
                variant=plan.name,
                reconfigurable_adc=plan.reconfigurable_adc,
                balance=BalanceStats(),
            )
        layers.append(metrics)
        total_latency += latency
        total_energy += energy
        traces.extend(trace_events)
    return layers, total_latency, total_energy, traces


def _off(opt: OptimizationConfig) -> OptimizationConfig:
    return opt.disabled_for_baseline()


def _movement_only(opt: OptimizationConfig) -> OptimizationConfig:
    return opt.with_overrides(
        enable_column_exchange=False,
        enable_row_exchange=False,
        enable_split=False,
        enable_optimized_allocation=True,
        enable_tree_reduction=True,
        enable_latency_sort=True,
        enable_input_prefetch=True,
        enable_profit_guard=False,
    )


def _balance_only(
    opt: OptimizationConfig,
    *,
    column: bool = False,
    row: bool = False,
    split: bool = False,
) -> OptimizationConfig:
    return opt.with_overrides(
        enable_column_exchange=column,
        enable_row_exchange=row,
        enable_split=split,
        enable_optimized_allocation=False,
        enable_tree_reduction=False,
        enable_latency_sort=False,
        enable_input_prefetch=False,
        enable_profit_guard=False,
    )


def _full_balance(opt: OptimizationConfig) -> OptimizationConfig:
    return opt.with_overrides(
        enable_column_exchange=True,
        enable_row_exchange=True,
        enable_split=True,
        enable_optimized_allocation=False,
        enable_tree_reduction=False,
        enable_latency_sort=False,
        enable_input_prefetch=False,
        enable_profit_guard=False,
    )


def _variant_plans(config: SimulationConfig) -> list[VariantPlan]:
    base = config.optimizations
    if config.variants:
        plans: list[VariantPlan] = []
        for item in config.variants:
            flags = item.get("optimizations", {})
            plans.append(
                VariantPlan(
                    name=str(item["name"]),
                    reconfigurable_adc=bool(item.get("reconfigurable_adc", True)),
                    apply_balancing=bool(item.get("apply_balancing", False)),
                    optimizations=base.with_overrides(**flags),
                )
            )
        return plans

    suite = config.variant_suite.lower()
    if suite == "paper_ablation":
        return [
            VariantPlan("puma_fixed_adc", False, False, _off(base)),
            VariantPlan("sparse_puma", True, False, _off(base)),
            VariantPlan("col_exchange", True, True, _balance_only(base, column=True)),
            VariantPlan("row_exchange", True, True, _balance_only(base, row=True)),
            VariantPlan("split_mvmu", True, True, _balance_only(base, split=True)),
            VariantPlan("load_balance_all", True, True, _full_balance(base)),
            VariantPlan("data_movement", True, False, _movement_only(base)),
            VariantPlan("samba_full", True, True, base),
        ]
    return [
        VariantPlan("puma_fixed_adc", False, False, _off(base)),
        VariantPlan("sparse_puma", True, False, _off(base)),
        VariantPlan("samba", True, True, base),
    ]


def run_experiment(config: SimulationConfig) -> ExperimentResult:
    workload = build_workload(
        config.workload,
        seed=config.seed,
        crossbar_size=config.hardware.crossbar_size,
    )
    mapped_layers = [map_layer(layer, config.hardware) for layer in workload.layers]
    variants = _variant_plans(config)

    layer_metrics_by_variant: dict[str, list[LayerMetrics]] = {}
    totals: dict[str, tuple[float, float]] = {}
    all_traces: list[TraceEvent] = []
    for plan in variants:
        layer_metrics, latency, energy, traces = _simulate_variant(
            mapped_layers,
            config.hardware,
            plan=plan,
        )
        layer_metrics_by_variant[plan.name] = layer_metrics
        totals[plan.name] = (latency, energy)
        all_traces.extend(traces)

    base_latency, base_energy = totals["puma_fixed_adc"]
    summaries: list[VariantSummary] = []
    all_layers: list[LayerMetrics] = []
    for plan in variants:
        latency, energy = totals[plan.name]
        summaries.append(
            VariantSummary(
                variant=plan.name,
                latency_cycles=latency,
                energy_pj=energy,
                speedup_vs_fixed_adc=base_latency / latency if latency else 0.0,
                energy_efficiency_vs_fixed_adc=base_energy / energy if energy else 0.0,
            )
        )
        base_by_layer = {
            item.layer: item for item in layer_metrics_by_variant["puma_fixed_adc"]
        }
        for item in layer_metrics_by_variant[plan.name]:
            base = base_by_layer[item.layer]
            all_layers.append(
                LayerMetrics(
                    layer=item.layer,
                    variant=item.variant,
                    windows=item.windows,
                    blocks=item.blocks,
                    cores=item.cores,
                    tiles=item.tiles,
                    latency_cycles=item.latency_cycles,
                    energy_pj=item.energy_pj,
                    speedup_vs_fixed_adc=base.latency_cycles / item.latency_cycles
                    if item.latency_cycles
                    else 0.0,
                    energy_efficiency_vs_fixed_adc=base.energy_pj / item.energy_pj
                    if item.energy_pj
                    else 0.0,
                    balance=item.balance,
                    avg_core_latency_cycles=item.avg_core_latency_cycles,
                    bottleneck_core_cycles=item.bottleneck_core_cycles,
                    movement_cycles=item.movement_cycles,
                    utilization=item.utilization,
                    rearrange_vectors=item.rearrange_vectors,
                )
            )

    return ExperimentResult(
        workload=workload.name,
        hardware=asdict(config.hardware),
        variants=tuple(summaries),
        layers=tuple(all_layers),
        traces=tuple(all_traces[: config.trace_limit]),
    )


def load_config(path: str | Path) -> SimulationConfig:
    import json

    with Path(path).open("r", encoding="utf-8") as handle:
        return SimulationConfig.from_dict(json.load(handle))
