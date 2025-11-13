python ./generate_outcome_table.py ./aggregated_statistics.json --output ./outcome_table.tex
python ./generate_outcome_table.py ./aggregated_statistics_libmcs.json --output ./outcome_table_libmcs.tex
python ./generate_outcome_table.py ./aggregated_statistics_zlib.json --output ./outcome_table_zlib.tex
python ./generate_failing_table.py ./aggregated_statistics.json ./aggregated_statistics_libmcs.json ./aggregated_statistics_zlib.json
python ./generate_performance_table.py ./aggregated_performance.json ./aggregated_performance_libmcs.json ./aggregated_performance_zlib.json
