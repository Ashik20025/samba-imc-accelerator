"""Command line interface for the SAMBA simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from samba.design_space import run_design_space, write_design_space
from samba.reporting import write_reports
from samba.simulator import load_config, run_experiment
from samba.suite import run_suite


def _run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    result = run_experiment(config)
    write_reports(result, args.out)
    print(f"Wrote SAMBA report to {Path(args.out).resolve()}")
    for summary in result.variants:
        print(
            f"{summary.variant}: "
            f"latency={summary.latency_cycles:.2f} cycles, "
            f"energy={summary.energy_pj:.2f} pJ, "
            f"speedup={summary.speedup_vs_fixed_adc:.3f}x"
        )
    return 0


def _parse_int_list(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip()]


def _sweep(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    rows = run_design_space(
        config,
        crossbar_sizes=_parse_int_list(args.crossbar_sizes),
        cores_per_tile=_parse_int_list(args.cores_per_tile),
        mvmus_per_core=_parse_int_list(args.mvmus_per_core),
    )
    write_design_space(rows, args.out)
    print(f"Wrote SAMBA design-space sweep to {Path(args.out).resolve()}")
    return 0


def _suite(args: argparse.Namespace) -> int:
    config_paths = [item.strip() for item in args.configs.split(",") if item.strip()]
    rows = run_suite(config_paths, args.out)
    print(f"Wrote SAMBA final suite to {Path(args.out).resolve()}")
    for row in rows:
        if "samba" in row.variant:
            print(
                f"{row.experiment} / {row.variant}: "
                f"speedup={row.speedup_vs_fixed_adc:.3f}x, "
                f"energy_eff={row.energy_efficiency_vs_fixed_adc:.3f}x"
            )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SAMBA IMC accelerator simulator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run", help="run an experiment config")
    run_parser.add_argument("--config", required=True, help="path to a JSON experiment config")
    run_parser.add_argument("--out", required=True, help="output directory for reports")
    run_parser.set_defaults(func=_run)
    sweep_parser = subparsers.add_parser("sweep", help="run a hardware design-space sweep")
    sweep_parser.add_argument("--config", required=True, help="path to a JSON experiment config")
    sweep_parser.add_argument("--out", required=True, help="output directory for sweep reports")
    sweep_parser.add_argument("--crossbar-sizes", default="32,64", help="comma-separated crossbar sizes")
    sweep_parser.add_argument("--cores-per-tile", default="4,8", help="comma-separated core counts")
    sweep_parser.add_argument("--mvmus-per-core", default="4,8", help="comma-separated MVMU counts")
    sweep_parser.set_defaults(func=_sweep)
    suite_parser = subparsers.add_parser("suite", help="run multiple configs and aggregate results")
    suite_parser.add_argument(
        "--configs",
        required=True,
        help="comma-separated JSON config paths",
    )
    suite_parser.add_argument("--out", required=True, help="output directory for aggregate suite")
    suite_parser.set_defaults(func=_suite)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
