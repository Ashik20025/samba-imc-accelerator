"""Full project suite runner and aggregate reporting."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from samba.reporting import write_reports
from samba.simulator import ExperimentResult, load_config, run_experiment


@dataclass(frozen=True)
class SuiteRow:
    experiment: str
    variant: str
    latency_cycles: float
    energy_pj: float
    speedup_vs_fixed_adc: float
    energy_efficiency_vs_fixed_adc: float
    layer_count: int
    report_path: str


@dataclass(frozen=True)
class ValidationFinding:
    level: str
    experiment: str
    message: str


def run_suite(config_paths: list[str | Path], out_dir: str | Path) -> list[SuiteRow]:
    out_path = Path(out_dir)
    runs_dir = out_path / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    rows: list[SuiteRow] = []

    for config_path in config_paths:
        config_file = Path(config_path)
        config = load_config(config_file)
        result = run_experiment(config)
        run_dir = runs_dir / config_file.stem
        write_reports(result, run_dir)
        experiment_name = f"{config_file.stem} ({result.workload})"
        rows.extend(_rows_for_result(result, run_dir, experiment_name=experiment_name))

    write_suite_outputs(rows, out_path)
    return rows


def write_suite_outputs(rows: list[SuiteRow], out_dir: str | Path) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    findings = validate_suite(rows)
    (out_path / "suite_summary.json").write_text(
        json.dumps(
            {
                "runs": [asdict(row) for row in rows],
                "validation": [asdict(item) for item in findings],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_suite_csv(rows, out_path / "suite_summary.csv")
    (out_path / "executive_summary.md").write_text(
        _suite_markdown(rows, findings),
        encoding="utf-8",
    )
    (out_path / "index.html").write_text(_suite_html(rows, findings), encoding="utf-8")


def validate_suite(rows: list[SuiteRow]) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    experiments = sorted({row.experiment for row in rows})
    for experiment in experiments:
        group = [row for row in rows if row.experiment == experiment]
        variants = {row.variant for row in group}
        if "puma_fixed_adc" not in variants:
            findings.append(ValidationFinding("error", experiment, "Missing fixed ADC baseline."))
        for row in group:
            if row.latency_cycles <= 0 or row.energy_pj <= 0:
                findings.append(
                    ValidationFinding("error", experiment, f"{row.variant} has non-positive metrics.")
                )
        samba = _best_samba(group)
        sparse = _variant(group, "sparse_puma")
        if samba and sparse and samba.speedup_vs_fixed_adc + 1e-9 < sparse.speedup_vs_fixed_adc:
            findings.append(
                ValidationFinding(
                    "warning",
                    experiment,
                    "SAMBA speedup is below sparse-only baseline; inspect profit guard and movement constants.",
                )
            )
        if samba and samba.speedup_vs_fixed_adc < 1.0:
            findings.append(
                ValidationFinding("warning", experiment, "SAMBA is slower than fixed ADC baseline.")
            )
    if not findings:
        findings.append(ValidationFinding("ok", "suite", "All sanity checks passed."))
    return findings


def _rows_for_result(
    result: ExperimentResult,
    run_dir: Path,
    *,
    experiment_name: str,
) -> list[SuiteRow]:
    layer_count = len({item.layer for item in result.layers})
    return [
        SuiteRow(
            experiment=experiment_name,
            variant=summary.variant,
            latency_cycles=summary.latency_cycles,
            energy_pj=summary.energy_pj,
            speedup_vs_fixed_adc=summary.speedup_vs_fixed_adc,
            energy_efficiency_vs_fixed_adc=summary.energy_efficiency_vs_fixed_adc,
            layer_count=layer_count,
            report_path=str((run_dir / "index.html").resolve()),
        )
        for summary in result.variants
    ]


def _write_suite_csv(rows: list[SuiteRow], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SuiteRow.__dataclass_fields__))
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def _variant(rows: list[SuiteRow], name: str) -> SuiteRow | None:
    return next((row for row in rows if row.variant == name), None)


def _best_samba(rows: list[SuiteRow]) -> SuiteRow | None:
    samba_rows = [row for row in rows if "samba" in row.variant]
    if not samba_rows:
        return None
    return max(samba_rows, key=lambda row: row.speedup_vs_fixed_adc)


def _headline_rows(rows: list[SuiteRow]) -> list[SuiteRow]:
    selected: list[SuiteRow] = []
    for experiment in sorted({row.experiment for row in rows}):
        group = [row for row in rows if row.experiment == experiment]
        samba = _best_samba(group)
        if samba:
            selected.append(samba)
    return selected


def _suite_markdown(rows: list[SuiteRow], findings: list[ValidationFinding]) -> str:
    lines = [
        "# SAMBA Final Suite Executive Summary",
        "",
        "## Main Claim",
        "",
        "The simulator evaluates a PUMA-style fixed ADC baseline, a sparse reconfigurable ADC baseline, and SAMBA optimizations for sparse analog in-memory-computing inference.",
        "",
        "## Headline Results",
        "",
        "| Experiment | Best SAMBA Variant | Layers | Speedup | Energy Efficiency | Report |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in _headline_rows(rows):
        lines.append(
            f"| {row.experiment} | {row.variant} | {row.layer_count} | {row.speedup_vs_fixed_adc:.3f}x | {row.energy_efficiency_vs_fixed_adc:.3f}x | [open]({row.report_path}) |"
        )

    lines.extend(
        [
            "",
            "## Full Variant Table",
            "",
            "| Experiment | Variant | Latency Cycles | Energy pJ | Speedup | Energy Eff. |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row.experiment} | {row.variant} | {row.latency_cycles:,.2f} | {row.energy_pj:,.2f} | {row.speedup_vs_fixed_adc:.3f}x | {row.energy_efficiency_vs_fixed_adc:.3f}x |"
        )

    lines.extend(["", "## Validation", ""])
    for finding in findings:
        lines.append(f"- `{finding.level}` `{finding.experiment}`: {finding.message}")
    lines.extend(
        [
            "",
            "## What To Show",
            "",
            "1. Start with this executive summary.",
            "2. Open the full ResNet50 dashboard for the largest workload.",
            "3. Open the VGG19 ablation dashboard to explain which SAMBA components help.",
            "4. Show `trace.csv` to demonstrate the project models core/tile execution, not only final numbers.",
            "",
        ]
    )
    return "\n".join(lines)


def _bar_svg(rows: list[SuiteRow], *, metric: str) -> str:
    headline = _headline_rows(rows)
    if not headline:
        return ""
    values = [
        (
            row.experiment[:34],
            row.speedup_vs_fixed_adc
            if metric == "speedup"
            else row.energy_efficiency_vs_fixed_adc,
        )
        for row in headline
    ]
    width = 980
    left = 280
    row_h = 34
    height = 44 + len(values) * row_h
    max_value = max(value for _, value in values) or 1.0
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    parts.append(
        '<style>.lbl{font:13px system-ui;fill:#172033}.val{font:12px system-ui;fill:#46536a}.bar{fill:#2f6fed}.good{fill:#13a37f}</style>'
    )
    for index, (name, value) in enumerate(values):
        y = 24 + index * row_h
        bar_w = int((width - left - 100) * value / max_value)
        klass = "good" if metric == "energy" else "bar"
        parts.append(f'<text class="lbl" x="0" y="{y + 15}">{name}</text>')
        parts.append(f'<rect class="{klass}" x="{left}" y="{y}" width="{bar_w}" height="20" rx="4"></rect>')
        parts.append(f'<text class="val" x="{left + bar_w + 10}" y="{y + 15}">{value:.3f}x</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def _suite_html(rows: list[SuiteRow], findings: list[ValidationFinding]) -> str:
    headline_rows = "".join(
        "<tr>"
        f"<td>{row.experiment}</td>"
        f"<td>{row.variant}</td>"
        f"<td>{row.layer_count}</td>"
        f"<td>{row.speedup_vs_fixed_adc:.3f}x</td>"
        f"<td>{row.energy_efficiency_vs_fixed_adc:.3f}x</td>"
        f'<td><a href="{row.report_path}">open</a></td>'
        "</tr>"
        for row in _headline_rows(rows)
    )
    finding_rows = "".join(
        f"<tr><td>{item.level}</td><td>{item.experiment}</td><td>{item.message}</td></tr>"
        for item in findings
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SAMBA Final Suite</title>
  <style>
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #172033;
      background: #f5f7fb;
    }}
    header {{
      padding: 34px clamp(22px, 4vw, 64px);
      background: #fff;
      border-bottom: 1px solid #d9dee8;
    }}
    main {{
      padding: 28px clamp(22px, 4vw, 64px) 64px;
      display: grid;
      gap: 24px;
    }}
    h1 {{ margin: 0; font-size: clamp(28px, 4vw, 44px); letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; letter-spacing: 0; }}
    p {{ color: #5d6980; max-width: 920px; line-height: 1.55; }}
    section {{
      background: #fff;
      border: 1px solid #d9dee8;
      border-radius: 8px;
      padding: 22px;
      overflow-x: auto;
    }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 24px; }}
    table {{ border-collapse: collapse; width: 100%; min-width: 760px; font-size: 14px; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #d9dee8; text-align: right; white-space: nowrap; }}
    th:first-child, td:first-child, th:nth-child(2), td:nth-child(2), th:nth-child(3), td:nth-child(3) {{ text-align: left; }}
    th {{ color: #5d6980; background: #fbfcff; }}
    a {{ color: #2f6fed; text-decoration: none; font-weight: 650; }}
  </style>
</head>
<body>
  <header>
    <h1>SAMBA Final Suite</h1>
    <p>Aggregate results across microbenchmarks, VGG19, and ResNet50 workloads. This is the main page to open when presenting the project.</p>
  </header>
  <main>
    <section>
      <h2>Headline Results</h2>
      <table>
        <thead><tr><th>Experiment</th><th>SAMBA Variant</th><th>Layers</th><th>Speedup</th><th>Energy Efficiency</th><th>Report</th></tr></thead>
        <tbody>{headline_rows}</tbody>
      </table>
    </section>
    <div class="grid">
      <section><h2>Best SAMBA Speedup</h2>{_bar_svg(rows, metric="speedup")}</section>
      <section><h2>Best SAMBA Energy Efficiency</h2>{_bar_svg(rows, metric="energy")}</section>
    </div>
    <section>
      <h2>Validation</h2>
      <table>
        <thead><tr><th>Level</th><th>Experiment</th><th>Message</th></tr></thead>
        <tbody>{finding_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
