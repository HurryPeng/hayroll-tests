# Hayroll Tests

`metadata.json` contains metadata about each program in the CRUST benchmark, and is used to run the transpilation and tests.

The current results of the benchmark can be viewed at [`benchmark_summary.json`](./benchmark_summary.json).

## Prerequisites

Requires `CBench` directory from the [CRUST benchmark](https://github.com/anirudhkhatry/CRUST-bench/tree/c56fc7a67ea00c95a3fce4061e90cc8c99d071ec/datasets) to be copied into this repository.

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
