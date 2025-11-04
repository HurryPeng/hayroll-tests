#!/usr/bin/env python3
"""Generate a LaTeX performance table from aggregated stage metrics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, List


DEFAULT_OUTPUT = Path("performance_table.tex")

STAGE_LAYOUT = [
	("Pioneer", "Pioneer (symbolic eval)"),
	("Splitter", "Splitter"),
	("Maki", "Maki (C macro analysis)"),
	("Seeder", "Seeder"),
	("C2Rust", "C2Rust"),
	("Reaper", "Reaper"),
	("Merger", "Merger"),
	("Cleaner", "Cleaner"),
]


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Render LaTeX table rows from aggregated performance JSON files."
	)
	parser.add_argument(
		"inputs",
		nargs="+",
		type=Path,
		help="Aggregated performance JSON files (one per table column).",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=DEFAULT_OUTPUT,
		help=f"Output LaTeX path (default: {DEFAULT_OUTPUT}).",
	)
	return parser.parse_args(list(argv))


def load_performance(path: Path) -> dict:
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def ms_string(value: float) -> str:
	return str(int(round(value)))


def percent_string(value: float) -> str:
	return str(int(round(value * 100)))


def build_stage_entry(stage_data: dict, stage_key: str) -> str:
	ms_key = stage_key
	ratio_key = f"{stage_key}_ratio"
	if ms_key not in stage_data or ratio_key not in stage_data:
		raise KeyError(f"Stage data missing required keys: {ms_key} / {ratio_key}")
	ms_value = ms_string(stage_data[ms_key])
	percent_value = percent_string(stage_data[ratio_key])
	return f"{ms_value} ({percent_value}\\%)"


def build_column_entries(content: dict) -> List[str]:
	stage_data = content.get("stages")
	if not isinstance(stage_data, dict):
		raise ValueError("Input JSON must contain a 'stages' object.")

	entries: List[str] = []
	for stage_key, _label in STAGE_LAYOUT:
		entries.append(build_stage_entry(stage_data, stage_key))

	total_ms = content.get("total_ms")
	if total_ms is None:
		raise ValueError("Input JSON must include 'total_ms'.")
	entries.append(f"{ms_string(total_ms)} (100\\%)")
	return entries


def render_table(columns: List[List[str]]) -> str:
	column_headers = [f"\\textbf{{Placeholder {idx}}}" for idx in range(1, len(columns) + 1)]

	header_line = "\\textbf{Component}"
	if column_headers:
		header_line += " & " + " & ".join(column_headers)
	header_line += " \\\\"  # end of line in LaTeX

	lines: List[str] = [
		"\\begin{table}[t]",
		"\\centering",
		"\\caption{Pipeline performance per component (ms/CU, share of total runtime).}",
		"\\label{tab:perf}",
		f"\\begin{{tabular}}{{l{'r' * len(columns)}}}",
		"\\toprule",
		header_line,
		"\\midrule",
	]

	for index, (stage_key, label) in enumerate(STAGE_LAYOUT):
		row_entries = [column[index] for column in columns]
		row_line = f"{label}"
		if row_entries:
			row_line += " & " + " & ".join(row_entries)
		row_line += " \\\\"  # stage row
		lines.append(row_line)

	lines.append("\\addlinespace")

	aggregate_entries = [f"\\textbf{{{column[-1]}}}" for column in columns]
	aggregate_line = "\\textbf{Aggregate}"
	if aggregate_entries:
		aggregate_line += " & " + " & ".join(aggregate_entries)
	aggregate_line += " \\\\"  # aggregate row
	lines.append(aggregate_line)

	lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
	return "\n".join(lines)


def main(argv: Iterable[str]) -> int:
	args = parse_args(argv)

	columns = [build_column_entries(load_performance(path)) for path in args.inputs]

	table_text = render_table(columns)
	args.output.write_text(table_text, encoding="utf-8")
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

