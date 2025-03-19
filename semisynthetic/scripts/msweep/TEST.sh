#!/bin/bash
set -e
source settings.sh


cd ${BASE_DIR}/scripts

mut_ratio=3.0
replicate=1
n_reads=50000
trial=1
bash msweep/run_pseudoalignment.sh $mut_ratio $replicate $n_reads $trial
bash msweep/run_msweep.sh $mut_ratio $replicate $n_reads $trial 0
bash msweep/run_msweep.sh $mut_ratio $replicate $n_reads $trial 1
bash msweep/run_msweep.sh $mut_ratio $replicate $n_reads $trial 2
bash msweep/run_msweep.sh $mut_ratio $replicate $n_reads $trial 3
bash msweep/run_msweep.sh $mut_ratio $replicate $n_reads $trial 4
