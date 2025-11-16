# Hayroll Tests

Automated test runner for validating C to Rust transpilation using the C2Rust toolchain.
It builds, transpiles, and tests C programs from the CRUST benchmark, summarizing results in a structured JSON file.

The current results of the benchmark can be viewed at [`test_results.json`](test_results.json).

`metadata-filtered.json` contains metadata about each program in the CRUST benchmark, and is used to run the transpilation and tests.

## Prerequisites

Requires installing [Hayroll](https://github.com/UW-HARVEST/Hayroll) and its dependencies. Please refer to the Hayroll repository for installation instructions. To make sure you are testing the latest Hayroll and its latest dependencies, please clone the main branch of the Hayroll repository, and when running `prerequisites.bash`, add `--latest`. You do not need to lean how to use Hayroll for this benchmark; the scripts will handle everything.

Requires `CBench` directory from the [CRUST benchmark]. To copy:
```sh
./fetch-CBench.bash
```

Other dependencies include: `python3`, `bear`, `make`, `gcc`, `cargo`, `c2rust`.

## Usage

To transpile all C programs and run their tests:

```sh
python3 scripts/run_tests.py
```

To generate metadata used to run tests:

```sh
python3 scripts/generate_metadata.py
```

To view the pass rate (generates `benchmark_summary.json`):

```sh
python analyze.py
```

To view effectiveness and performance results (generates `aggregated_performance.json` and `aggregated_statistics.json`):

```sh
python aggregate_reports.py
```

To generate the LaTeX outcome table:

```sh
python generate_outcome_table.py aggregated_statistics.json
```

To generate the LaTeX performance table:

```sh
python generate_performance_table.py aggregated_performance.json
```

## Notes

Currently excluding `skp` program because it always seems to hang.
