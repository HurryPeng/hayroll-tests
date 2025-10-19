import json
from pathlib import Path


def load_json(path: Path):
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def main():
	repo_root = Path(__file__).resolve().parent
	summary_path = repo_root / "benchmark_summary.json"
	metadata_path = repo_root / "metadata.json"
	output_path = repo_root / "metadata-filtered.json"

	summary = load_json(summary_path)
	metadata = load_json(metadata_path)

	failing = {
		name
		for name, payload in summary.items()
		if payload.get("status") != "passed"
	}

	programs = metadata.get("programs", [])
	filtered_programs = [entry for entry in programs if entry.get("name") not in failing]

	metadata["programs"] = filtered_programs

	with output_path.open("w", encoding="utf-8") as handle:
		json.dump(metadata, handle, indent=2)
		handle.write("\n")

	removed = len(programs) - len(filtered_programs)
	print(f"Removed {removed} failing program(s).")


if __name__ == "__main__":
	main()
