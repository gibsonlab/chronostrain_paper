from pathlib import Path
import json
from typing import List

import click

import numpy as np
from numpy.random import Generator
import pandas as pd


def load_poppunk_cluster(cluster_csv: Path) -> pd.DataFrame:
    def fix_accession(t_id):
        tokens = t_id.split('_')
        return '{}.{}'.format('_'.join(tokens[:-1]), tokens[2])

    df = pd.read_csv(cluster_csv)
    df['Accession'] = df['Taxon'].map(fix_accession)
    return df.drop(columns=['Taxon'])


def load_chronostrain_cluster(chronostrain_cluster: Path) -> pd.DataFrame:
    df_entries = []
    with open(chronostrain_cluster, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            tokens = line.strip().split("\t")
            rep_id = tokens[0]
            members = tokens[1].split(",")
            for member in members:
                df_entries.append({
                    'Accession': member,
                    'Cluster': rep_id
                })
    return pd.DataFrame(df_entries)


def load_strainge_cluster(strainge_cluster: Path) -> pd.DataFrame:
    df_entries = []
    with open(strainge_cluster, "rt") as f:
        for line in f:
            clust = line.strip().split('\t')
            rep = clust[0]
            for member in clust:
                df_entries.append({
                    'Accession': member,
                    'Cluster': rep
                })
    return pd.DataFrame(df_entries)


def parse_phylogroups(phylogroup_path: Path):
    df_entries = []
    with open(phylogroup_path, 'rt') as f:
        for line in f:
            tokens = line.strip().split('\t')
            accession = Path(tokens[0]).with_suffix('').with_suffix('').name
            phylogroup = tokens[4]
            df_entries.append({'Accession': accession, 'Phylogroup': phylogroup})
    return pd.DataFrame(df_entries)


def generate_cluster_df(chronostrain_cluster_tsv: Path, poppunk_cluster_csv: Path, strainge_cluster_file: Path, phylogroup_path: Path):
    poppunk_df = load_poppunk_cluster(poppunk_cluster_csv)
    chronostrain_df = load_chronostrain_cluster(chronostrain_cluster_tsv)
    strainge_df = load_strainge_cluster(strainge_cluster_file)
    phylogroup_df = parse_phylogroups(phylogroup_path)

    res = poppunk_df.merge(
        poppunk_df.groupby("Cluster")['Accession'].count().rename('SizePopPUNK'), left_on='Cluster',
        right_index=True
    ).rename(columns={'Cluster': 'ClusterPopPUNK'})

    res = res.merge(
        chronostrain_df.rename(columns={'Cluster': 'ClusterChronoStrain'}), on='Accession'
    ).merge(
        chronostrain_df.groupby("Cluster")['Accession'].count().rename('SizeChronoStrain'),
        left_on='ClusterChronoStrain', right_index=True
    )

    res = res.merge(
        strainge_df.rename(columns={'Cluster': 'ClusterStrainGE'}), on='Accession'
    ).merge(
        strainge_df.groupby("Cluster")['Accession'].count().rename('SizeStrainGE'),
        left_on='ClusterStrainGE', right_index=True
    )

    # Attach phylogroup information
    res = res.merge(
        phylogroup_df, on='Accession', how='left'
    ).fillna('?').merge(
        phylogroup_df.rename(columns={'Phylogroup': 'PhylogroupChronoStrain', 'Accession': 'ClusterRight'}),
        right_on='ClusterRight', left_on='ClusterChronoStrain', how='left'
    ).drop(columns=['ClusterRight']).set_index('Accession')
    return res


def sample_random(cluster_df: pd.DataFrame, size: int, rng: Generator) -> List[str]:
    weights = np.sqrt((1/3) * (np.square(cluster_df['SizeChronoStrain']) + np.square(cluster_df['SizePopPUNK']) + np.square(cluster_df['SizeStrainGE'])))
    weights = 1 / weights
    weights = weights * (cluster_df['PhylogroupChronoStrain'] == 'A')  # Clusters have zero weight if not phylogroup A

    random_accs = []
    pool = cluster_df.loc[cluster_df['Phylogroup'] == 'A']  # The possible pool to select from are phylogroup A genomes.
    for i in range(size):
        selection = pool.sample(1, weights=weights, random_state=rng)
        selection_poppunk = selection['ClusterPopPUNK'].item()
        selection_chronostrain = selection['ClusterChronoStrain'].item()
        selection_strainge = selection['ClusterStrainGE'].item()

        # Add the selection.
        acc = selection.index[0]
        random_accs.append(acc)

        # Remove the respective clusters.
        pool = pool.loc[
            (pool['ClusterPopPUNK'] != selection_poppunk)
            & (pool['ClusterChronoStrain'] != selection_chronostrain)
            & (pool['ClusterStrainGE'] != selection_strainge)
        ]
    rng.shuffle(random_accs)
    return random_accs


@click.command()
@click.option(
    '--index-path', '-i', 'index_path',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True), required=True,
)
@click.option(
    '--poppunk-clusters', '-p', 'poppunk_csv',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True), required=True,
)
@click.option(
    '--chronostrain-clusters', '-c', 'chronostrain_cluster_tsv',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True), required=True,
)
@click.option(
    '--strainge-clusters', '-sg', 'strainge_cluster_path',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True), required=True,
)
@click.option(
    '--phylogroups', '-ph', 'phylogroup_path',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True), required=True,
)
@click.option('--num-genomes', '-n', 'num_genomes', type=int, required=True)
@click.option('--seed', '-s', 'seed', type=int, required=True)
@click.option(
    '--abundance-csv', '-a', 'abundance_path',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True), required=True
)
@click.option(
    '--out', '-o', 'out_dir',
    type=click.Path(path_type=Path, file_okay=False), required=True
)
def main(index_path: Path,
         poppunk_csv: Path,
         chronostrain_cluster_tsv: Path,
         strainge_cluster_path: Path,
         phylogroup_path: Path,
         num_genomes: int, seed: int,
         abundance_path: Path,
         out_dir: Path):
    index_df = pd.read_csv(index_path, sep='\t')
    cluster_df = generate_cluster_df(chronostrain_cluster_tsv, poppunk_csv, strainge_cluster_path, phylogroup_path)
    rng = np.random.default_rng(seed)
    print("Sampling random strain IDs.")
    random_strain_ids = sample_random(cluster_df, size=num_genomes, rng=rng)

    out_dir.mkdir(exist_ok=True, parents=True)
    acc_list_path = out_dir / 'target_genomes.txt'
    with open(acc_list_path, 'wt') as f:
        print("## SEED={}".format(seed), file=f)
        for x in random_strain_ids:
            print(x, file=f)

    for x in random_strain_ids:
        src_seq_path = Path(index_df.loc[index_df['Accession'] == x, 'SeqPath'].item())
        tgt_seq_path = out_dir / f'{x}.fasta'
        tgt_seq_path.unlink(missing_ok=True)
        tgt_seq_path.symlink_to(src_seq_path)

    tgt_abundance_path = out_dir / 'abundances.txt'
    with open(tgt_abundance_path, "wt") as out_f, open(abundance_path, "rt") as template_f:
        template_f.readline()
        print(",".join(
            ["T"] + [f'{x}.READSIM_MUTANT' for x in random_strain_ids]
        ), file=out_f)
        for line in template_f:
            print(line.strip(), file=out_f)


if __name__ == "__main__":
    main()

