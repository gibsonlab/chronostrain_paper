#!/bin/bash
set -e
source settings.sh
source mgems/settings.sh

rerun_demix_sample()
{
  infant_id=$1
  sample_id=$2

  echo "[*] Re-running demix_check for ${infant_id}, ${sample_id}"
  strain_outdir=${DATA_DIR}/${infant_id}/mgems/${sample_id}/Efaecalis
  strain_refdir=${DATA_DIR}/database/mgems/ref_dir/Efaecalis
  demix_check --mode_check \
    --binned_reads_dir ${strain_outdir}/binned_reads \
    --msweep_abun ${strain_outdir}/msweep_abundances.txt \
    --out_dir ${strain_outdir}/demix_check \
    --ref ${strain_refdir}


#  filt_abund_file=demix_check/msweep_abundances_filt.tsv
#  echo "${analysis_dir}/${filt_abund_file}"
#  while IFS=$'\t' read cluster abundance
#  do
#    if [ "${cluster}" == "cluster" ]; then continue; fi
#    echo "Rerunning demix_check on cluster ${cluster} inside ${analysis_dir}"
#    check_reads.sh \
#    --cluster "${cluster}" \
#    --abundances ${analysis_dir}/msweep_abundances.txt \
#    --threads 6 \
#    --tmpdir ./TMP \
#    --fwd ${analysis_dir}/binned_reads/${cluster}_1.fastq.gz \
#    --rev ${analysis_dir}/binned_reads/${cluster}_2.fastq.gz \
#    --reference /mnt/e/infant_nt/database/mgems/ref_dir/Efaecalis
#  done < ${analysis_dir}/${filt_abund_file}
}


rerun_demix_infant()
{
  infant_id=$1
  for mgem_dir in ${DATA_DIR}/${infant_id}/mgems; do
    while IFS=$'\t' read -r p_id timepoint sample_id fq1 fq2; do
      if [ -f ${DATA_DIR}/${infant_id}/mgems/${sample_id}/mgems.${sample_id}.DONE ]; then
        rerun_demix_sample "${infant_id}" "${sample_id}"
      fi
#      if [ -f ./${infant_id}/mgems/${sample_id}/mgems.${sample_id}.DONE ]; then
#          if ! [ -f ./${infant_id}/mgems/${sample_id}/Efaecalis/demix_check.tsv ]; then
#            echo "Need to fix ${infant_id}, ${sample_id}"
#            rm ./${infant_id}/mgems/${sample_id}/mgems.${sample_id}.DONE
#            rm -f ./${infant_id}/mgems/mgems.DONE
#          else
#            echo "${infant_id}, ${sample_id} is fine"
#          fi
#      fi
    done < ${DATA_DIR}/${infant_id}/dataset.tsv
#    echo "Rerunning read binning + QC in ${f}..."
#    bash mgems/run_pipeline_infant.sh ${infant_id}
  done
}


mkdir -p ./TMP
#rerun_demix_infant "A00021_T1"

while read infant_id
do
  if ! [ -f ${DATA_DIR}/${infant_id}/mgems/mgems.DONE ]; then continue; fi
  rerun_demix_infant "${infant_id}"
done < "${INFANT_ID_LIST}"
