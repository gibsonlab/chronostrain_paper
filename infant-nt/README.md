# About

An analysis pipeline of the dataset provided by 2019 Shao et al.
- Dataset publication title: Stunted microbiota and opportunistic pathogen colonization in caesarean-section birth
  - DOI: https://doi.org/10.1038/s41586-019-1560-1
  - Link: https://www.nature.com/articles/s41586-019-1560-1

# Additional Requirements 

These are already included in the "full" conda recipe `conda_full.yml`.

- FastMLST (https://github.com/EnzoAndree/FastMLST)
- pigz
- KneadData
- (Requirements from `database` example)

# Important note about KneadData & Trimmomatic interaction on linux conda-forge setup

If one runs into the KneadData error that the jarfile for trimmomatic is invalid or corrupt, one needs to
edit `trimmomatic_jar=“trimmomatic*` to `trimmomatic_jar=trimmomatic.jar` in python script `<CONDA_ENV>/kneaddata/lib/<PYTHON>/site-packages/kneaddata/config.py` to explicitly point
to the jar file instead of the executable python wrapper.

# Pipeline walkthrough

All scripts are meant to be run from within the `scripts` subdirectory (so first do `cd scripts`)

Files are downloaded to the directory pointed to by the `DATA_DIR` environment variable, specified in `settings.sh`.


## 1. Download the dataset.

```bash
bash dataset/download_assembly_catalog.sh  # Download isolate assembly ENA metadata
bash dataset/download_metagenomic_catalog.sh  # Download metagenomic dataset ENA metadata
bash dataset/download_all.sh  # Download all participants' metagenomic reads for which an isolate exists, and run them through KneadData
bash dataset/download_assemblies.sh  # Runs a for loop to download all assemblies. Automatically invokes fastMLST.
```

Note that `download_all.sh` invokes `download_dataset.sh`, which handles downloading the reads from
a particular participant. It can be manually invoked to download a particular slice of the data (e.g. infant A01653):
```bash
# Assumes ENA metadata have been downloaded
bash dataset/download_dataset.sh A01653
bash ../helpers/process_dataset.sh A01653  # invoke kneaddata/trimmomatic pipeline.
```

## 2. Set up the database.

The user has two options: generate databases from scratch, or download pre-geneated database files from Zenodo.
(https://zenodo.org/records/10932690).
In either case, please follow these instructions.

## 2.1 Option 1: Download from Zenodo
If extracting from Zenodo, please extract (`tar -xvzf`) the following files:
1. `ELMC_chronostrain_db.tar.gz`
2. `ELMC_chronostrain_db_MUT002.tar.gz`
3. `ELMC_mgems_db.tar.gz`
4. `ELMC_mgems_db_MUt002.tar.gz`
5. `ELMC_fastmlst.tar.gz`
This will extract the contents into a subdirectory called `infant_nt`.
Then, move the `database` subdirectory into your chosen DATA_DIR:
```
source settings.sh; mv infant_nt/database $DATA_DIR/
```

Then, download `themisto_640k.tar` archive from Zenodo: https://zenodo.org/records/7736981.
Extract its contents into `$DATA_DIR/database/mgems/themisto_640k`, so that this directory contains the index files (e.g. `index.tdbg`).


## 2.2 Option 2: Create from scratch

First, grab the European E.faecalis isolate genomes from Pöntinen et al. (https://pubmed.ncbi.nlm.nih.gov/33750782/). 
Note that the raw fastQ files are uploaded under BioProject PRJEB28327; please contact those authors for the pre-assembled contigs.
After this download, please run `scripts/database/create_european_efaec_index.py` to catalog those genomes' metadata into a chronostrain-readable TSV file.

Next, set up the chronostrain database from scratch.
Use the provided `efaecalis` recipe in the `database` example. 
Ensure that it is configured to use the database directories that match this example.
Then, run the notebook "database_efaecalis_elmc.ipynb" in the `infant-nt/notebooks` subdirectory and execute all cells.

To set up the mGEMS database, ensure that you do this AFTER the above (chronostrain database creation).
Next, run the script `mgems/make_chronostrain_mirror_db.sh`.
Then, download `themisto_640k.tar` archive from Zenodo: https://zenodo.org/records/7736981.
Extract its contents into `$DATA_DIR/database/mgems/themisto_640k`, so that this directory contains the index files (e.g. `index.tdbg`).

To make the mutated dtabases, run `mutations/make_mutation_dbs.sh`.

Finally, please run `fastmlst` on all genomes (BabyBiome isolates, RefSeq isolates and European isolates)
via the script `database/run_fastmlst.sh`.


## 3. Perform analysis

There are two scripts to use; either will suit the purpose just fine.
To run the analysis using an already-downloaded dataset (e.g. assuming step 1 has finished), use the batch script
```bash
bash run_chronostrain_all.sh
```

Or, to perform analysis on a single participant (e.g. infant A01653)
```bash
bash run_chronostrain_all.sh A01653
```
Both scripts call the individual ingredients (e.g. `chronotrain filter`, `chronostrain advi`).

*Note: The analysis was originally done on an RTX 3090 which has 24GB of memory. 
If using a different GPU, one can tweak the memory usage requirements directly through `settings.sh`.
To reduce memory footprint, reduce `CHRONOSTRAIN_NUM_SAMPLES` and/or reduce `CHRONOSTRAIN_READ_BATCH_SZ`.*
