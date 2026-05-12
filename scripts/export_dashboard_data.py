#!/usr/bin/env python3
"""Export simulator artifacts into a compact dashboard data file."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_PATH = ROOT / "artifacts" / "final_suite" / "suite_summary.json"
RUNS_DIR = ROOT / "artifacts" / "final_suite" / "runs"
OUT_PATH = ROOT / "dashboard" / "public" / "data" / "dashboard.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_layers(metrics: dict) -> list[dict]:
    layers = metrics.get("layers", [])
    samba_layers = [item for item in layers if "samba" in item["variant"]]
    if not samba_layers:
        samba_layers = layers
    top = sorted(samba_layers, key=lambda item: item["latency_cycles"], reverse=True)[:12]
    return [
        {
            "layer": item["layer"],
            "variant": item["variant"],
            "latency_cycles": item["latency_cycles"],
            "energy_pj": item["energy_pj"],
            "speedup": item["speedup_vs_fixed_adc"],
            "movement_cycles": item.get("movement_cycles", 0),
            "utilization": item.get("utilization", 0),
            "column_swaps": item.get("balance", {}).get("column_swaps", 0),
            "row_swaps": item.get("balance", {}).get("row_swaps", 0),
            "split_mvmus": item.get("balance", {}).get("split_mvmus", 0),
        }
        for item in top
    ]


def load_experiments() -> list[dict]:
    experiments: list[dict] = []
    for metrics_path in sorted(RUNS_DIR.glob("*/metrics.json")):
        metrics = load_json(metrics_path)
        run_name = metrics_path.parent.name
        experiments.append(
            {
                "run_name": run_name,
                "workload": metrics["workload"],
                "variants": metrics["variants"],
                "top_layers": summarize_layers(metrics),
                "trace_count": len(metrics.get("traces", [])),
                "report_path": str((metrics_path.parent / "index.html").resolve()),
            }
        )
    return experiments


def main() -> int:
    if not SUITE_PATH.exists():
        raise SystemExit(f"Missing suite summary: {SUITE_PATH}")
    suite = load_json(SUITE_PATH)
    payload = {
        "generated_from": str(SUITE_PATH.resolve()),
        "suite": suite,
        "experiments": load_experiments(),
        "notes": [
            "Results are architectural simulation outputs, not chip measurements.",
            "Speedup and energy efficiency are normalized to fixed ADC PUMA-style baseline.",
            "SAMBA combines sparse ADC precision, profitable load balancing, and data-movement scheduling.",
        ],
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
