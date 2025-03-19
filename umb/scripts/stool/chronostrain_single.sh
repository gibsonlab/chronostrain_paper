#!/bin/bash
set -e

source settings.sh

# =========== Run chronostrain. ==================
echo "Running inference."

umb_id="UMB18"
echo "[*] Running inference on ${umb_id}, without time-series prior."

for t in 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16; do
  echo "[*] Handling timepoint ${t}."
  run_dir=${OUTPUT_DIR}/${umb_id}_split/${t}
  breadcrumb=${run_dir}/inference.DONE

  if [ -f $breadcrumb ]; then
    echo "[*] Skipping inference for ${umb_id}."
  else
    echo "[*] Running inference for ${umb_id}, timepoint #${t}"
    export CHRONOSTRAIN_LOG_FILEPATH=${run_dir}/logs/chronostrain_inference.log
    export CHRONOSTRAIN_CACHE_DIR=${run_dir}/chronostrain/cache
    mkdir -p ${run_dir}/chronostrain

    chronostrain advi \
      -r ${run_dir}/filtered/filtered_reads.csv \
      -o ${run_dir}/chronostrain \
      --correlation-mode $CHRONOSTRAIN_CORR_MODE \
      --iters $CHRONOSTRAIN_NUM_ITERS \
      --epochs $CHRONOSTRAIN_NUM_EPOCHS \
      --decay-lr $CHRONOSTRAIN_DECAY_LR \
      --lr-patience ${CHRONOSTRAIN_LR_PATIENCE} \
      --loss-tol ${CHRONOSTRAIN_LOSS_TOL} \
      --learning-rate ${CHRONOSTRAIN_LR} \
      --num-samples $CHRONOSTRAIN_NUM_SAMPLES \
      --read-batch-size $CHRONOSTRAIN_READ_BATCH_SZ \
      --min-lr ${CHRONOSTRAIN_MIN_LR} \
      --plot-format "pdf" \
      --plot-elbo \
      --prune-strains \
      --with-zeros \
      --prior-p 0.001 \
      --accumulate-gradients

    touch $breadcrumb
  fi
done
# ================================================
