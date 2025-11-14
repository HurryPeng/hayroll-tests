#!/bin/bash

echo "Fetching CRUST_bench.zip"
wget -q https://raw.github.com/anirudhkhatry/CRUST-bench/main/datasets/CRUST_bench.zip
echo "Unpacking CBench"
unzip -q CRUST_bench.zip "CBench/*"
rm CRUST_bench.zip
