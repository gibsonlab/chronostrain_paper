# About

This subdirectory contains the scripts for reproducing the semisynthetic benchmark dataset and results.

# 1. Step 1: Prepare method-specific databases

For reproducibility, please download the relevant pre-constructed databases from Zenodo: (todo insert link).

## 1.1 ChronoStrain

Please extract the ChronoStrain database archive.
Ensure that the extracted directory contains: `ecoli.json`, `ecoli.clusters.txt` and a subdirectory named `__ecoli_`.

Next, add this extracted directory to the shell script `settings.sh`.
The variable name is `CHRONOSTRAIN_DB_DIR_SRC` (ctrl+f search for this variable name).
```bash
export CHRONOSTRAIN_DB_DIR_SRC=<your extracted archive dir>
```

## 1.2 mGEMS

Please extract the mGEMS database archive, which only contains a species-level Ecoli themisto index. 
As stated on the Zenodo page, please grab the full 640k pan-genome index separately from https://zenodo.org/records/7736981.

Next, add these two directories to the shell script `settings.sh`. 
The variable names are `SPECIES_REF_DIR` for the 640k genome index, and `ECOLI_REF_DIR` for the smaller ecoli-specific index from our Zenodo record.

## 1.3 StrainGE

Please extract the StrainGE database archive, ensuring it contains a file called `clusters.tsv`.
Next, add these two directories to the shell script `settings.sh`.
The variable name is `STRAINGE_DB_DIR`.

## 1.4 StrainEst

After extracting, ensure that the StrainEst archive contains the subdirectories `metagenomic_alignment_db` and `snv_profiling_db`. 
The variable name is `STRAINEST_DB_DIR`.

## 1.5 (Optional alternative) Generating database from scratch

For a summary to how the databases were created, refer to the methods section of the main text.
To generate databases from scratch using a fresh set of latest NCBI genomes, please follow this pipeline:
- `ecoli.ipynb` (in database/complete_recipes) -- downloads a fresh catalog of genomes from `NCBI datasets` and constructs a chronostrain database.
- `mgems/create_ecoli_db.sh` -- Uses the above genome index, restricts to E.coli, and constructs a themisto index.
- `strainest/prepare_strainest.sh` -- (note: StrainEst requires python2 to run.) Picks a genome representative and performs SNP profiling.
- `strainge/prepare_straingst.sh` -- extracts Ecoli/Shigella from the reference index and creates a kmer set.

# 2. Simulated Data

## 2.1 Download and extract the reads.

The reads can also be downloaded from the Zenodo archive, and extracted with `zstd`.
```bash
tar --zstd -xvf reads.tar.zst
```
Then, ensure that the variable `DATA_DIR` inside settings.sh points to the folder containing the reads.
This folder should contain the `mutratio_*` and `background` subdirectories.

## 2.2 (Optional alternative) Simulate the reads from scratch

Ensure that the databases above have been using the final option (1.5 -- generating database from scratch), so that
the genome assemblies have been downloaded and catalogued (`index.tsv`, pointed to by the environment variable `REFSEQ_INDEX` in `settings.sh`)

Ensure that the variable `DATA_DIR` inside `settings.sh` points to your desired location for generating the entire dataset and storing the analysis outputs.
Once you have done that, run the following two commands:
```bash
# pick genomes and mutate them across multiple replicates.
bash dataset/prepare_all_replicates.sh

# for each genome, simulate reads using ART across 5 read depths and 2 different seeds.
# This script also downloads background (real) reads and preprocesses them using kneaddata.
bash dataset/simulate_reads.sh
```

Note 1: `simulate_reads.sh` requires two dependencies: `kneaddata` (for adapter trimming and removing contaminations) and `fastq-tools` (to invoke `fastq-sort`).

Note 2: The archive `reads.tar.zst` on Zenodo was created using the command: `find . \( -path "*/background/sorted/*.fq" -o -path "*/mutratio_*/replicate_*/reads_*/trial_*/reads/*.fq" \) -print0 | tar --zstd -cvf reads.tar.zst --null -T -`

# 3. Run analyses

```bash
# Perform necessary pre-caching for chronostrain's database (for runtime consistency)
bash chronostrain/preload_all.sh

bash chronostrain/analyze_all.sh
bash mgems/analyze_all.sh
bash strainest/run_strainest_all.sh
bash strainge/run_straingst_all.sh
```

# 4. Render results

To render the results into plots, start a jupyter server and open the notebook `notebooks/evaluation_semisynthetic.ipynb`.
Run all the cells one-by-one. 

(Note: at the top of the notebook, there is a cell containing the database locations. Those need to be updated to mirror the above steps!)