"""Design-space exploration for SAMBA hardware parameters."""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from pathlib import Path

from samba.architecture import HardwareConfig, SimulationConfig
from samba.simulator import run_experiment


@dataclass(frozen=True)
class SweepRow:
    crossbar_size: int
    cores_per_tile: int
    mvmus_per_core: int
    variant: str
    latency_cycles: float
    energy_pj: float
    speedup_vs_fixed_adc: float
    energy_efficiency_vs_fixed_adc: float


def run_design_space(
    config: SimulationConfig,
    *,
    crossbar_sizes: list[int],
    cores_per_tile: list[int],
    mvmus_per_core: list[int],
) -> list[SweepRow]:
    rows: list[SweepRow] = []
    for crossbar in crossbar_sizes:
        for cores in cores_per_tile:
            for mvmus in mvmus_per_core:
                hardware = replace(
                    config.hardware,
                    crossbar_size=crossbar,
                    cores_per_tile=cores,
                    mvmus_per_core=mvmus,
                )
                hardware.validate()
                point_config = SimulationConfig(
                    seed=config.seed,
                    hardware=hardware,
                    optimizations=config.optimizations,
                    workload=config.workload,
                    variants=config.variants,
                    variant_suite=config.variant_suite,
                    trace_limit=0,
                )
                result = run_experiment(point_config)
                for summary in result.variants:
                    rows.append(
                        SweepRow(
                            crossbar_size=crossbar,
                            cores_per_tile=cores,
                            mvmus_per_core=mvmus,
                            variant=summary.variant,
                            latency_cycles=summary.latency_cycles,
                            energy_pj=summary.energy_pj,
                            speedup_vs_fixed_adc=summary.speedup_vs_fixed_adc,
                            energy_efficiency_vs_fixed_adc=summary.energy_efficiency_vs_fixed_adc,
                        )
                    )
    return rows


def write_design_space(rows: list[SweepRow], out_dir: str | Path) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    csv_path = out_path / "design_space.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SweepRow.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)
    (out_path / "design_space.md").write_text(_design_space_md(rows), encoding="utf-8")


def _design_space_md(rows: list[SweepRow]) -> str:
    lines = [
        "# SAMBA Design-Space Sweep",
        "",
        "| Crossbar | Cores/Tile | MVMUs/Core | Variant | Latency | Energy | Speedup | Energy Eff. |",
        "|---:|---:|---:|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {crossbar} | {cores} | {mvmus} | {variant} | {latency:,.2f} | {energy:,.2f} | {speedup:.3f}x | {eff:.3f}x |".format(
                crossbar=row.crossbar_size,
                cores=row.cores_per_tile,
                mvmus=row.mvmus_per_core,
                variant=row.variant,
                latency=row.latency_cycles,
                energy=row.energy_pj,
                speedup=row.speedup_vs_fixed_adc,
                eff=row.energy_efficiency_vs_fixed_adc,
            )
        )
    best = _best_samba(rows)
    if best is not None:
        lines.extend(
            [
                "",
                "## Best SAMBA Point",
                "",
                f"- Crossbar size: `{best.crossbar_size}`",
                f"- Cores per tile: `{best.cores_per_tile}`",
                f"- MVMUs per core: `{best.mvmus_per_core}`",
                f"- Speedup: `{best.speedup_vs_fixed_adc:.3f}x`",
                f"- Energy efficiency: `{best.energy_efficiency_vs_fixed_adc:.3f}x`",
                "",
            ]
        )
    return "\n".join(lines)


def _best_samba(rows: list[SweepRow]) -> SweepRow | None:
    samba_rows = [row for row in rows if "samba" in row.variant]
    if not samba_rows:
        return None
    return max(samba_rows, key=lambda row: (row.speedup_vs_fixed_adc, row.energy_efficiency_vs_fixed_adc))
