# Hayroll Tests

`metadata-filtered.json` contains metadata about each program in the CRUST benchmark, and is used to run the transpilation and tests.

The current results of the benchmark can be viewed at [`benchmark_summary.json`](./benchmark_summary.json).

## Prerequisites

Requires installing [Hayroll](https://github.com/UW-HARVEST/Hayroll) and its dependencies. Please refer to the Hayroll repository for installation instructions. To make sure you are testing the latest Hayroll and its latest dependencies, please clone the main branch of the Hayroll repository, and when running `prerequisites.bash`, add `--latest`. You do not need to lean how to use Hayroll for this benchmark; the scripts will handle everything.

Requires `CBench` directory from the [CRUST benchmark]. To copy:
```sh
./fetch-CBench.bash
```

## Usage

To transpile and run tests:

```sh
python benchmark.py
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
