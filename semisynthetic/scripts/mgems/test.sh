#!/bin/bash
set -e
source settings.sh

cd ${BASE_DIR}/scripts

mutation_ratio=1.0
replicate=1
n_reads=40000
trial=1

bash mgems/analyze_sample_species.sh $mutation_ratio $replicate $n_reads $trial 0 "mgems" 0.65

bash mgems/analyze_sample_strain.sh $mutation_ratio $replicate $n_reads $trial 0 "mgems" 0.65

bash mgems/run_demix_check.sh $mutation_ratio $replicate $n_reads $trial 0 "mgems" 0.65
