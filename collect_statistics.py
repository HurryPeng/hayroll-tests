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


def find_statistics_files(search_root: Path) -> Iterable[Path]:
	"""Yield every statistics.json living directly under a hayroll_out directory."""

	for path in search_root.rglob(STATISTICS_FILENAME):
		if path.parent.name == "hayroll_out":
			yield path



def accumulate_statistics(paths: Iterable[Path]) -> Tuple[Dict[str, object], int, List[str]]:
	totals: Dict[str, float] = {}
	non_numeric: Dict[str, object] = {}
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

			if isinstance(value, Real):
				totals[key] = totals.get(key, 0) + value
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
			combined[key] = totals[key]
		elif key in non_numeric:
			combined[key] = non_numeric[key]
		else:
			combined[key] = None

	return combined, file_count, ratio_keys


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
	return parser.parse_args(argv)


def main(argv: Iterable[str]) -> int:
	args = parse_args(argv)

	anchor = Path(__file__).resolve()
	search_root = args.search_root
	if search_root is None:
		search_root = anchor.parent / "CBench"
	search_root = search_root.resolve()

	if not search_root.exists():
		raise SystemExit(f"Search root {search_root} does not exist.")

	statistics_files = sorted(find_statistics_files(search_root))
	if not statistics_files:
		print("No statistics.json files found.", file=sys.stderr)
		print(json.dumps({"count": 0}, indent=args.indent, sort_keys=args.sort_keys))
		return 0

	combined, file_count, ratio_keys = accumulate_statistics(statistics_files)
	combined["count"] = file_count
	final_stats = recompute_ratios(combined, ratio_keys)

	output_text = json.dumps(final_stats, indent=args.indent, sort_keys=args.sort_keys)

	if args.output:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		args.output.write_text(output_text + "\n", encoding="utf-8")

	print(output_text)
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))

