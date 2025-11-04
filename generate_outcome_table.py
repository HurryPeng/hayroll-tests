#!/usr/bin/env python3
"""Generate a LaTeX macro outcome table from aggregated statistics."""

from __future__ import annotations

import argparse
import json
import sys
from numbers import Real
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_OUTPUT = Path("outcome_table.tex")


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Render macro outcome LaTeX table from aggregated statistics JSON."
	)
	parser.add_argument("input", type=Path, help="Aggregated statistics JSON file")
	parser.add_argument(
		"--output",
		type=Path,
		default=DEFAULT_OUTPUT,
		help=f"Output LaTeX path (default: {DEFAULT_OUTPUT}).",
	)
	return parser.parse_args(list(argv))


def load_statistics(path: Path) -> Dict[str, object]:
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def to_int(value: Real | None) -> int:
	if value is None:
		return 0
	return int(round(float(value)))


def to_percent(value: Real | None) -> int:
	if value is None:
		return 0
	return int(round(float(value) * 100))


def compute_ratio(
	count: Real | None, ratio_value: Real | None, total: Real | None
) -> Real | None:
	if isinstance(ratio_value, Real):
		return ratio_value
	if not isinstance(count, Real) or not isinstance(total, Real):
		return None
	if float(total) == 0:
		return None
	return float(count) / float(total)


def format_entry(count: Real | None, ratio: Real | None) -> str:
	return f"{to_int(count)} ({to_percent(ratio)}\\%)"


def build_table(stats: Dict[str, object]) -> str:
	labels: List[str] = [
		"All",
		"Syntactical",
		"Expr.",
		"Stmt.",
		"Decl.",
		"Type",
		"Non-syn.",
	]

	section_total = {
		"All": stats.get("macro"),
		"Syntactical": stats.get("macro_syntactic"),
		"Expr.": stats.get("macro_expr"),
		"Stmt.": stats.get("macro_stmt"),
		"Decl.": stats.get("macro_decl"),
		"Type": stats.get("macro_typeloc"),
		"Non-syn.": stats.get("macro_non_syntactic"),
	}

	translated = {
		"All": stats.get("macro_seeded"),
		"Syntactical": stats.get("macro_syntactic_seeded"),
		"Expr.": stats.get("macro_expr_seeded"),
		"Stmt.": stats.get("macro_stmt_seeded"),
		"Decl.": stats.get("macro_decl_seeded"),
		"Type": stats.get("macro_typeloc_seeded"),
		"Non-syn.": stats.get("macro_non_syntactic_seeded"),
	}

	translated_ratio = {
		label: compute_ratio(
			translated[label],
			stats.get(
				{
					"All": "macro_seeded_ratio",
					"Syntactical": "macro_syntactic_seeded_ratio",
					"Expr.": "macro_expr_seeded_ratio",
					"Stmt.": "macro_stmt_seeded_ratio",
					"Decl.": "macro_decl_seeded_ratio",
					"Type": "macro_typeloc_seeded_ratio",
					"Non-syn.": "macro_non_syntactic_seeded_ratio",
				}[label]
			),
			section_total[label],
		)
		for label in labels
	}

	translated_fn = {
		"All": stats.get("macro_seeded_fn"),
		"Syntactical": stats.get("macro_syntactic_seeded_fn"),
		"Expr.": stats.get("macro_expr_seeded_fn"),
		"Stmt.": stats.get("macro_stmt_seeded_fn"),
		"Decl.": stats.get("macro_decl_seeded_fn"),
		"Type": stats.get("macro_typeloc_seeded_fn"),
		"Non-syn.": stats.get("macro_non_syntactic_seeded_fn"),
	}

	translated_fn_ratio = {
		label: compute_ratio(
			translated_fn[label],
			stats.get(
				{
					"All": "macro_seeded_fn_ratio",
					"Syntactical": "macro_syntactic_seeded_fn_ratio",
					"Expr.": "macro_expr_seeded_fn_ratio",
					"Stmt.": "macro_stmt_seeded_fn_ratio",
					"Decl.": "macro_decl_seeded_fn_ratio",
					"Type": "macro_typeloc_seeded_fn_ratio",
					"Non-syn.": "macro_non_syntactic_seeded_fn_ratio",
				}[label]
			),
			translated[label],
		)
		for label in labels
	}

	translated_macro = {
		"All": stats.get("macro_seeded_macro"),
		"Syntactical": stats.get("macro_syntactic_seeded_macro"),
		"Expr.": stats.get("macro_expr_seeded_macro"),
		"Stmt.": stats.get("macro_stmt_seeded_macro"),
		"Decl.": stats.get("macro_decl_seeded_macro"),
		"Type": stats.get("macro_typeloc_seeded_macro"),
		"Non-syn.": stats.get("macro_non_syntactic_seeded_macro"),
	}

	translated_macro_ratio = {
		label: compute_ratio(
			translated_macro[label],
			stats.get(
				{
					"All": "macro_seeded_macro_ratio",
					"Syntactical": "macro_syntactic_seeded_macro_ratio",
					"Expr.": "macro_expr_seeded_macro_ratio",
					"Stmt.": "macro_stmt_seeded_macro_ratio",
					"Decl.": "macro_decl_seeded_macro_ratio",
					"Type": "macro_typeloc_seeded_macro_ratio",
					"Non-syn.": "macro_non_syntactic_seeded_macro_ratio",
				}[label]
			),
			translated[label],
		)
		for label in labels
	}

	left_expanded = {
		"All": stats.get("macro_rejected"),
		"Syntactical": stats.get("macro_syntactic_rejected"),
		"Expr.": stats.get("macro_expr_rejected"),
		"Stmt.": stats.get("macro_stmt_rejected"),
		"Decl.": stats.get("macro_decl_rejected"),
		"Type": stats.get("macro_typeloc"),
		"Non-syn.": stats.get("macro_non_syntactic"),
	}

	left_expanded_ratio = {
		label: compute_ratio(
			left_expanded[label],
			stats.get(
				{
					"All": "macro_rejected_ratio",
					"Syntactical": "macro_syntactic_rejected_ratio",
					"Expr.": "macro_expr_rejected_ratio",
					"Stmt.": "macro_stmt_rejected_ratio",
					"Decl.": "macro_decl_rejected_ratio",
					"Type": "macro_typeloc_ratio",
					"Non-syn.": "macro_non_syntactic_ratio",
				}[label]
			),
			section_total[label],
		)
		for label in labels
	}

	headers = [
		"\\textbf{Outcome}",
		"\\textbf{All}",
		"\\textbf{Syntactical}",
		"\\textbf{Expr.}",
		"\\textbf{Stmt.}",
		"\\textbf{Decl.}",
		"\\textbf{Type}",
		"\\textbf{Non-syn.}",
	]

	def row_from(values: Dict[str, object]) -> str:
		return " & ".join(str(to_int(values[label])) for label in labels)

	table_lines = [
		"\\begin{table}[t]",
		"\\centering",
		"\\caption{Macro translation outcomes for PLACEHOLDER by syntactic category}",
		"\\label{tab:macro-outcomes-placeholders}",
		"\\resizebox{\\linewidth}{!}{",
		"\\begin{tabular}{lrrrrrrr}",
		"\\toprule",
		" & ".join(headers) + " \\\\",
		"\\midrule",
		"Total macros & " + row_from(section_total) + " \\\\[2pt]",
		"Successfully translated & "
		+ " & ".join(
			format_entry(translated[label], translated_ratio[label]) for label in labels
		)
		+ " \\\\",
		"\\quad$\\rightarrow$ Rust function & "
		+ " & ".join(
			format_entry(translated_fn[label], translated_fn_ratio[label])
			for label in labels
		)
		+ " \\\\",
		"\\quad$\\rightarrow$ Rust macro & "
		+ " & ".join(
			format_entry(translated_macro[label], translated_macro_ratio[label])
			for label in labels
		)
		+ " \\\\",
		"Left expanded & "
		+ " & ".join(
			format_entry(left_expanded[label], left_expanded_ratio[label])
			for label in labels
		)
		+ " \\\\",
		"\\bottomrule",
		"\\end{tabular}}",
		"\\end{table}",
		"",
	]

	return "\n".join(table_lines)


def main(argv: Iterable[str]) -> int:
	args = parse_args(argv)
	stats = load_statistics(args.input)
	table_text = build_table(stats)
	args.output.write_text(table_text, encoding="utf-8")
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

