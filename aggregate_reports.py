#!/usr/bin/env python3
"""Aggregate Hayroll statistics across the CBench corpus."""

from __future__ import annotations

import argparse
import json
import sys
from numbers import Real
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


STATISTICS_FILENAME = "statistics.json"
PERFORMANCE_FILENAME = "performance.json"


def normalize_total(value: float) -> float | int:
	if value.is_integer():
		return int(value)
	return value


def find_statistics_files(search_root: Path) -> Iterable[Path]:
	"""Yield every statistics.json living directly under a hayroll_out directory."""

	for path in search_root.rglob(STATISTICS_FILENAME):
		if path.parent.name.startswith("hayroll_out"):
			yield path


def find_performance_files(search_root: Path) -> Iterable[Path]:
	"""Yield every performance.json living directly under a hayroll_out directory."""

	for path in search_root.rglob(PERFORMANCE_FILENAME):
		if path.parent.name.startswith("hayroll_out"):
			yield path





def accumulate_statistics(paths: Iterable[Path]) -> Tuple[Dict[str, object], int, List[str]]:
	totals: Dict[str, float] = {}
	non_numeric: Dict[str, object] = {}
	nested_totals: Dict[str, Dict[str, float]] = {}
	nested_non_numeric: Dict[str, Dict[str, object]] = {}
	nested_key_order: Dict[str, List[str]] = {}
	nested_seen_keys: Dict[str, set[str]] = {}
	ratio_keys: List[str] = []
	ratio_seen: set[str] = set()
	key_order: List[str] = []
	seen_keys: set[str] = set()
	file_count = 0

	for stats_path in paths:
		with stats_path.open("r", encoding="utf-8") as handle:
			data = json.load(handle)

		file_count += 1
		for key, value in data.items():
			if key not in seen_keys:
				key_order.append(key)
				seen_keys.add(key)

			if key.endswith("_ratio"):
				if key not in ratio_seen:
					ratio_keys.append(key)
					ratio_seen.add(key)
				continue

			if value is None:
				continue

			if isinstance(value, dict):
				target_totals = nested_totals.setdefault(key, {})
				target_non_numeric = nested_non_numeric.setdefault(key, {})
				order = nested_key_order.setdefault(key, [])
				seen_nested = nested_seen_keys.setdefault(key, set())
				for inner_key, inner_value in value.items():
					if inner_key not in seen_nested:
						order.append(inner_key)
						seen_nested.add(inner_key)

					if inner_value is None:
						continue

					if isinstance(inner_value, Real):
						existing = target_totals.get(inner_key, 0.0)
						target_totals[inner_key] = existing + float(inner_value)
					else:
						stored_nested = target_non_numeric.get(inner_key)
						if stored_nested is None:
							target_non_numeric[inner_key] = inner_value
						elif stored_nested != inner_value:
							raise ValueError(
								f"Conflicting values for non-numeric field {key!r}[{inner_key!r}]: {stored_nested!r} vs {inner_value!r}"
							)
				continue

			if isinstance(value, Real):
				existing = totals.get(key, 0.0)
				totals[key] = existing + float(value)
			else:

				stored = non_numeric.get(key)
				if stored is None:
					non_numeric[key] = value
				elif stored != value:
					raise ValueError(
						f"Conflicting values for non-numeric field {key!r}: {stored!r} vs {value!r}"
					)

	combined: Dict[str, object] = {}
	for key in key_order:
		if key in totals:
			combined[key] = normalize_total(totals[key])
		elif key in nested_key_order:
			totals_for_key = nested_totals.get(key, {})
			non_numeric_for_key = nested_non_numeric.get(key, {})
			nested_combined: Dict[str, object] = {}
			for inner_key in nested_key_order[key]:
				if inner_key in totals_for_key:
					nested_combined[inner_key] = normalize_total(totals_for_key[inner_key])
				elif inner_key in non_numeric_for_key:
					nested_combined[inner_key] = non_numeric_for_key[inner_key]
				else:
					nested_combined[inner_key] = None
			combined[key] = nested_combined
		elif key in non_numeric:
			combined[key] = non_numeric[key]
		else:
			combined[key] = None

	return combined, file_count, ratio_keys


def aggregate_performance(paths: Iterable[Path]) -> Dict[str, object]:
	stage_totals: Dict[str, float] = {}
	stage_weights: Dict[str, float] = {}
	stage_order: List[str] = []
	stage_seen: set[str] = set()
	total_task_weight = 0.0
	total_ms_weighted = 0.0
	total_ms_weight = 0.0
	file_count = 0

	for perf_path in paths:
		with perf_path.open("r", encoding="utf-8") as handle:
			data = json.load(handle)

		stages = data.get("stages")
		task_count = data.get("task_count")
		total_ms = data.get("total_ms")

		if not isinstance(stages, dict):
			raise ValueError(f"Performance file {perf_path} is missing stage data.")
		if not isinstance(task_count, Real):
			raise ValueError(f"Performance file {perf_path} has non-numeric task_count {task_count!r}.")

		weight = float(task_count)
		if weight < 0:
			raise ValueError(f"Performance file {perf_path} has negative task_count {task_count!r}.")

		file_count += 1
		total_task_weight += weight

		if isinstance(total_ms, Real):
			total_ms_weighted += float(total_ms) * weight
			total_ms_weight += weight

		for stage, value in stages.items():
			if stage not in stage_seen:
				stage_order.append(stage)
				stage_seen.add(stage)

			if value is None:
				continue

			if not isinstance(value, Real):
				raise ValueError(
					f"Performance file {perf_path} has non-numeric value {value!r} for stage {stage!r}."
				)

			stage_totals[stage] = stage_totals.get(stage, 0.0) + float(value) * weight
			stage_weights[stage] = stage_weights.get(stage, 0.0) + weight

	stage_avgs: Dict[str, float | None] = {}
	for stage in stage_order:
		weight = stage_weights.get(stage, 0.0)
		if weight == 0:
			stage_avgs[stage] = None
		else:
			stage_avgs[stage] = stage_totals.get(stage, 0.0) / weight

	total_stage_sum = sum(value for value in stage_avgs.values() if isinstance(value, Real))
	stage_output: Dict[str, object] = {}
	for stage in stage_order:
		value = stage_avgs[stage]
		if value is None:
			stage_output[stage] = None
			stage_output[f"{stage}_ratio"] = None
		else:
			stage_output[stage] = normalize_total(float(value))
			stage_output[f"{stage}_ratio"] = (value / total_stage_sum) if total_stage_sum else None

	total_ms_avg: float | None
	if total_ms_weight > 0:
		total_ms_avg = total_ms_weighted / total_ms_weight
	else:
		total_ms_avg = None

	result: Dict[str, object] = {
		"project_count": file_count,
		"task_count": normalize_total(float(total_task_weight)) if file_count else 0,
		"total_ms": normalize_total(float(total_ms_avg)) if total_ms_avg is not None else None,
		"stages": stage_output,
	}
	return result


def infer_denominator_key(numerator_key: str) -> str | None:
	if "_" not in numerator_key:
		return None
	return numerator_key.rsplit("_", 1)[0]


def recompute_ratios(
	combined: Dict[str, object], ratio_keys: Iterable[str]
) -> Dict[str, object]:
	result = dict(combined)
	for ratio_key in ratio_keys:
		numerator_key = ratio_key[: -len("_ratio")]
		denominator_key = infer_denominator_key(numerator_key)

		numerator = result.get(numerator_key)
		denominator = result.get(denominator_key) if denominator_key else None

		if not isinstance(numerator, Real) or not isinstance(denominator, Real):
			result[ratio_key] = None
			continue

		if denominator == 0:
			result[ratio_key] = None
			continue

		result[ratio_key] = float(numerator) / float(denominator)

	return result


def add_failing_reason_ratios(stats: Dict[str, object]) -> None:
	"""Enrich failing_reason counts with ratios relative to unseeded macros."""

	failing = stats.get("failing_reasons")
	macro_total = stats.get("macro")
	macro_seeded = stats.get("macro_seeded")

	if not isinstance(failing, dict):
		return
	if not isinstance(macro_total, Real) or not isinstance(macro_seeded, Real):
		return

	denominator = macro_total - macro_seeded
	new_map: Dict[str, object] = {}
	for reason, count in failing.items():
		ratio_key = f"{reason}_ratio"
		ratio_value: float | None
		if not isinstance(count, Real) or denominator == 0:
			ratio_value = None
		else:
			ratio_value = float(count) / float(denominator)

		new_map[reason] = count
		new_map[ratio_key] = ratio_value

	stats["failing_reasons"] = new_map


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Collect and merge HayRoll statistics across CBench projects."
	)
	parser.add_argument(
		"--search-root",
		type=Path,
		help="Directory to search (defaults to the nearest ancestor that contains CBench).",
	)
	parser.add_argument(
		"--output",
		type=Path,
        default="aggregated_statistics.json",
		help="Optional file path to write the aggregated statistics JSON to.",
	)
	parser.add_argument(
		"--indent",
		type=int,
		default=2,
		help="Indentation level for JSON output (default: 2).",
	)
	parser.add_argument(
		"--sort-keys",
		action="store_true",
		help="Sort JSON object keys alphabetically in the output.",
	)
	return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
	args = parse_args(argv)

	anchor = Path(__file__).resolve()
	search_root = args.search_root
	if search_root is None:
		search_root = anchor.parent / "CBench"
	search_root = search_root.resolve()

	if not search_root.exists():
		raise SystemExit(f"Search root {search_root} does not exist.")

	performance_files = sorted(find_performance_files(search_root))
	performance_summary = aggregate_performance(performance_files)
	performance_output = args.output.parent / "aggregated_performance.json"
	performance_text = json.dumps(performance_summary, indent=args.indent, sort_keys=args.sort_keys)
	performance_output.parent.mkdir(parents=True, exist_ok=True)
	performance_output.write_text(performance_text + "\n", encoding="utf-8")

	statistics_files = sorted(find_statistics_files(search_root))
	if not statistics_files:
		print("No statistics.json files found.", file=sys.stderr)
		print(json.dumps({"count": 0}, indent=args.indent, sort_keys=args.sort_keys))
		return 0

	combined, file_count, ratio_keys = accumulate_statistics(statistics_files)
	combined["count"] = file_count
	final_stats = recompute_ratios(combined, ratio_keys)
	add_failing_reason_ratios(final_stats)

	output_text = json.dumps(final_stats, indent=args.indent, sort_keys=args.sort_keys)

	if args.output:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		args.output.write_text(output_text + "\n", encoding="utf-8")

	print(output_text)
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

