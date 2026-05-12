"""Report writers for SAMBA experiments."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from samba.simulator import ExperimentResult


def write_reports(result: ExperimentResult, out_dir: str | Path) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "metrics.json").write_text(
        json.dumps(result.as_dict(), indent=2),
        encoding="utf-8",
    )
    _write_csv(result, out_path / "metrics.csv")
    _write_trace_csv(result, out_path / "trace.csv")
    (out_path / "report.md").write_text(_markdown_report(result), encoding="utf-8")
    (out_path / "index.html").write_text(_html_report(result), encoding="utf-8")


def _write_csv(result: ExperimentResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "layer",
                "variant",
                "windows",
                "blocks",
                "cores",
                "tiles",
                "latency_cycles",
                "energy_pj",
                "speedup_vs_fixed_adc",
                "energy_efficiency_vs_fixed_adc",
                "avg_core_latency_cycles",
                "bottleneck_core_cycles",
                "movement_cycles",
                "utilization",
                "rearrange_vectors",
                "column_swaps",
                "row_swaps",
                "split_mvmus",
            ],
        )
        writer.writeheader()
        for item in result.layers:
            row = asdict(item)
            balance = row.pop("balance")
            row.update(
                {
                    "column_swaps": balance["column_swaps"],
                    "row_swaps": balance["row_swaps"],
                    "split_mvmus": balance["split_mvmus"],
                }
            )
            writer.writerow(row)


def _write_trace_csv(result: ExperimentResult, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "layer",
                "variant",
                "op",
                "start_cycle",
                "end_cycle",
                "core_id",
                "tile_id",
                "detail",
            ],
        )
        writer.writeheader()
        for item in result.traces:
            writer.writerow(asdict(item))


def _markdown_report(result: ExperimentResult) -> str:
    lines = [
        f"# SAMBA Experiment Report: {result.workload}",
        "",
        "## Variant Summary",
        "",
        "| Variant | Latency Cycles | Energy pJ | Speedup | Energy Efficiency |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in result.variants:
        lines.append(
            "| {variant} | {latency:,.2f} | {energy:,.2f} | {speedup:.3f}x | {eff:.3f}x |".format(
                variant=item.variant,
                latency=item.latency_cycles,
                energy=item.energy_pj,
                speedup=item.speedup_vs_fixed_adc,
                eff=item.energy_efficiency_vs_fixed_adc,
            )
        )

    lines.extend(
        [
            "",
            "## Layer Metrics",
            "",
            "| Layer | Variant | Windows | Blocks | Cores | Tiles | Latency | Energy | Speedup | Util. | Move Cycles | ColEx | RowEx | Split |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for item in result.layers:
        lines.append(
            "| {layer} | {variant} | {windows} | {blocks} | {cores} | {tiles} | {latency:,.2f} | {energy:,.2f} | {speedup:.3f}x | {util:.2%} | {move:,.2f} | {col} | {row} | {split} |".format(
                layer=item.layer,
                variant=item.variant,
                windows=item.windows,
                blocks=item.blocks,
                cores=item.cores,
                tiles=item.tiles,
                latency=item.latency_cycles,
                energy=item.energy_pj,
                speedup=item.speedup_vs_fixed_adc,
                util=item.utilization,
                move=item.movement_cycles,
                col=item.balance["column_swaps"],
                row=item.balance["row_swaps"],
                split=item.balance["split_mvmus"],
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The fixed ADC variant models a conventional PUMA-style baseline. Sparse PUMA enables static reconfigurable ADC precision from weight sparsity. SAMBA adds compiler-time load balancing and data-movement scheduling.",
            "",
            "The model reports architectural trends rather than transistor-calibrated silicon results. Calibrate the constants in `configs/*.json` when measured ADC, interconnect, or VFU costs are available.",
            "",
        ]
    )
    return "\n".join(lines)


def _bar_svg(values: list[tuple[str, float]], *, width: int = 860, height: int = 260) -> str:
    if not values:
        return ""
    max_value = max(value for _, value in values) or 1.0
    left = 150
    top = 22
    row_h = 28
    svg_h = max(height, top * 2 + row_h * len(values))
    bars = [
        f'<svg viewBox="0 0 {width} {svg_h}" role="img" aria-label="Variant speedup chart">'
    ]
    bars.append(
        '<style>.label{font:13px system-ui;fill:#172033}.value{font:12px system-ui;fill:#3d4960}.grid{stroke:#d9dee8;stroke-width:1}.bar{fill:#2f6fed}.bar2{fill:#13a37f}</style>'
    )
    for idx, (name, value) in enumerate(values):
        y = top + idx * row_h
        bar_w = int((width - left - 90) * value / max_value)
        color_class = "bar2" if "samba" in name else "bar"
        bars.append(f'<text class="label" x="0" y="{y + 16}">{name}</text>')
        bars.append(f'<rect class="{color_class}" x="{left}" y="{y}" width="{bar_w}" height="18" rx="3"></rect>')
        bars.append(f'<text class="value" x="{left + bar_w + 8}" y="{y + 14}">{value:.3f}x</text>')
    bars.append("</svg>")
    return "\n".join(bars)


def _html_report(result: ExperimentResult) -> str:
    speed_values = [(item.variant, item.speedup_vs_fixed_adc) for item in result.variants]
    energy_values = [(item.variant, item.energy_efficiency_vs_fixed_adc) for item in result.variants]
    rows = []
    for item in result.variants:
        rows.append(
            "<tr>"
            f"<td>{item.variant}</td>"
            f"<td>{item.latency_cycles:,.2f}</td>"
            f"<td>{item.energy_pj:,.2f}</td>"
            f"<td>{item.speedup_vs_fixed_adc:.3f}x</td>"
            f"<td>{item.energy_efficiency_vs_fixed_adc:.3f}x</td>"
            "</tr>"
        )
    bottlenecks = sorted(result.layers, key=lambda item: item.latency_cycles, reverse=True)[:15]
    layer_rows = []
    for item in bottlenecks:
        layer_rows.append(
            "<tr>"
            f"<td>{item.layer}</td>"
            f"<td>{item.variant}</td>"
            f"<td>{item.latency_cycles:,.2f}</td>"
            f"<td>{item.movement_cycles:,.2f}</td>"
            f"<td>{item.utilization:.1%}</td>"
            f"<td>{item.balance['column_swaps']}</td>"
            f"<td>{item.balance['row_swaps']}</td>"
            f"<td>{item.balance['split_mvmus']}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SAMBA Report - {result.workload}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172033;
      --muted: #5d6980;
      --line: #d9dee8;
      --surface: #ffffff;
      --band: #f5f7fb;
      --accent: #2f6fed;
      --good: #13a37f;
    }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--band);
    }}
    header {{
      background: var(--surface);
      border-bottom: 1px solid var(--line);
      padding: 28px clamp(20px, 4vw, 56px);
    }}
    main {{
      padding: 28px clamp(20px, 4vw, 56px) 56px;
      display: grid;
      gap: 24px;
    }}
    h1, h2 {{
      margin: 0;
      letter-spacing: 0;
    }}
    h1 {{
      font-size: clamp(26px, 3vw, 40px);
    }}
    h2 {{
      font-size: 18px;
      margin-bottom: 14px;
    }}
    p {{
      color: var(--muted);
      max-width: 920px;
      line-height: 1.55;
    }}
    section {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 22px;
      overflow-x: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      min-width: 760px;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 12px;
      text-align: right;
      white-space: nowrap;
    }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2) {{
      text-align: left;
    }}
    th {{
      color: var(--muted);
      font-weight: 650;
      background: #fbfcff;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 24px;
    }}
    .metric {{
      display: inline-flex;
      gap: 10px;
      align-items: baseline;
      margin-right: 28px;
    }}
    .metric strong {{
      font-size: 22px;
    }}
    .metric span {{
      color: var(--muted);
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>SAMBA Experiment Report</h1>
    <p>{result.workload}. Fixed ADC baseline, sparse reconfigurable ADC, SAMBA load balancing, and data-movement scheduling are compared with configurable hardware constants.</p>
  </header>
  <main>
    <section>
      <h2>Variant Summary</h2>
      <table>
        <thead><tr><th>Variant</th><th>Latency Cycles</th><th>Energy pJ</th><th>Speedup</th><th>Energy Efficiency</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    <div class="grid">
      <section>
        <h2>Speedup vs Fixed ADC</h2>
        {_bar_svg(speed_values)}
      </section>
      <section>
        <h2>Energy Efficiency vs Fixed ADC</h2>
        {_bar_svg(energy_values)}
      </section>
    </div>
    <section>
      <h2>Top Layer Bottlenecks</h2>
      <table>
        <thead><tr><th>Layer</th><th>Variant</th><th>Latency</th><th>Movement</th><th>Utilization</th><th>ColEx</th><th>RowEx</th><th>Split</th></tr></thead>
        <tbody>{''.join(layer_rows)}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
