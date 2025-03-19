#!/bin/bash
set -e
source settings.sh

cd ${BASE_DIR}/scripts

trial=1
#for n_reads in "${SYNTHETIC_COVERAGES[@]}"; do
#  bash chronostrain/filter.sh $n_reads $trial
#  bash chronostrain/run_chronostrain.sh $n_reads $trial
#done

for n_reads in "${SYNTHETIC_COVERAGES[@]}"; do
  bash msweep/run_pseudoalignment.sh $n_reads $trial
  bash msweep/run_msweep.sh $n_reads 1 0
  bash msweep/run_msweep.sh $n_reads 1 1
  bash msweep/run_msweep.sh $n_reads 1 2
  bash msweep/run_msweep.sh $n_reads 1 3
  bash msweep/run_msweep.sh $n_reads 1 4
done
