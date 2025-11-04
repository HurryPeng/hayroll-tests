#!/usr/bin/env python3
"""Generate LaTeX table comparing macro failing reasons across benchmarks."""

from __future__ import annotations

import argparse
import json
import sys
from numbers import Real
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_OUTPUT = Path("failing_table.tex")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Render failing reason LaTeX table from aggregated statistics JSON files."
	)
	parser.add_argument(
		"inputs",
		nargs="+",
		type=Path,
		help="Aggregated statistics JSON files (one per table column).",
	)
	parser.add_argument(
		"--output",
		type=Path,
		default=DEFAULT_OUTPUT,
		help=f"Output LaTeX path (default: {DEFAULT_OUTPUT}).",
	)
	return parser.parse_args(list(argv))


def load_stats(path: Path) -> Dict[str, object]:
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def safe_ratio(count: Real | None, ratio_value: Real | None, total: Real | None) -> Real | None:
	if isinstance(ratio_value, Real):
		return ratio_value
	if not isinstance(count, Real) or not isinstance(total, Real):
		return None
	if float(total) == 0:
		return None
	return float(count) / float(total)


def fmt_count(value: Real | None) -> int:
	if value is None:
		return 0
	return int(round(float(value)))


def fmt_percent(value: Real | None) -> int:
	if value is None:
		return 0
	return int(round(float(value) * 100))


def build_reason_order(stats: Dict[str, object]) -> List[str]:
	failing = stats.get("failing_reasons")
	if not isinstance(failing, dict):
		raise ValueError("Input JSON must contain a 'failing_reasons' object.")

	sortable: List[tuple[float, str]] = []
	for key, value in failing.items():
		if key.endswith("_ratio"):
			continue
		if isinstance(value, Real):
			sortable.append((float(value), key))
		else:
			sortable.append((0.0, key))

	sortable.sort(key=lambda item: (-item[0], item[1]))
	return [key for _count, key in sortable]


def extract_column(stats: Dict[str, object], order: List[str]) -> List[str]:
	failing = stats.get("failing_reasons")
	if not isinstance(failing, dict):
		raise ValueError("Input JSON must contain a 'failing_reasons' object.")

	rejected_total = stats.get("macro_rejected")
	column: List[str] = []
	for reason in order:
		count = failing.get(reason)
		ratio = safe_ratio(
			count,
			failing.get(f"{reason}_ratio"),
			rejected_total,
		)
		entry = f"{fmt_count(count)} ({fmt_percent(ratio)}\\%)"
		column.append(entry)
	return column


def render_table(order: List[str], columns: List[List[str]]) -> str:
	headers = [f"\\textbf{{Placeholder {idx}}}" for idx in range(1, len(columns) + 1)]

	lines: List[str] = [
		"\\begin{table}[t]",
		"\\centering",
		"\\caption{Comparison of macro translation failing reasons across benchmarks. Percentages are relative to all rejected macros in each benchmark.}",
		"\\label{tab:failing-reasons}",
		f"\\begin{{tabular}}{{l{'r' * len(columns)}}}",
		"\\toprule",
	]

	header_line = "\\textbf{Failing reason}"
	if headers:
		header_line += " & " + " & ".join(headers)
	header_line += " \\\\"  # column headers
	lines.append(header_line)
	lines.append("\\midrule")

	for idx, reason in enumerate(order):
		row_entries = [column[idx] for column in columns]
		label = reason[:1].upper() + reason[1:]
		row = label
		if row_entries:
			row += " & " + " & ".join(row_entries)
		row += " \\\\"  # table row
		lines.append(row)

	lines.extend(["\\bottomrule", "\\end{tabular}", "\\end{table}", ""])
	return "\n".join(lines)


def main(argv: Iterable[str]) -> int:
	args = parse_args(argv)
	stats_list = [load_stats(path) for path in args.inputs]
	reason_order = build_reason_order(stats_list[0])

	columns = [extract_column(stats, reason_order) for stats in stats_list]

	table_text = render_table(reason_order, columns)
	args.output.write_text(table_text, encoding="utf-8")
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

