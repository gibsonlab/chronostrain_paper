from pathlib import Path
from typing import *

import numpy as np
import pandas as pd
import sklearn.metrics

from .base import trial_dir, parse_runtime, parse_phylogroups
from .ground_truth import load_ground_truth
from .error_metrics import rms, tv_error, compute_rank_corr, binned_rms, strain_split_rms


def extract_straingst_prediction(
        data_dir: Path,
        mut_ratio: str,
        replicate: int,
        read_depth: int,
        trial: int,
        time_points: List[float],
        cluster_path: Path,
        phylogroup_path: Path,
        subdir_name: str = 'straingst'
) -> Tuple[np.ndarray, np.ndarray, List[str], pd.DataFrame, int]:
    output_basedir = trial_dir(mut_ratio, replicate, read_depth, trial, data_dir) / 'output'

    cluster_df = load_straingst_cluster(cluster_path, phylogroup_path)
    cluster_ordering = sorted(pd.unique(cluster_df['Cluster']))

    output_dir = output_basedir / subdir_name
    if not output_dir.exists():
        raise FileNotFoundError(f"Output dir for mut_ratio={mut_ratio}, replicate={replicate}, read_depth={read_depth}, trial={trial} not found.")

    preds = np.zeros((len(time_points), len(cluster_ordering)), dtype=float)
    scores = np.zeros((len(time_points), len(cluster_ordering)), dtype=float)
    for t_idx in range(len(time_points)):
        t_path = output_dir / f'output_{t_idx}.strains.tsv'
        if t_path.exists():
            pred_t, scores_t = parse_straingst_pred_single(t_path, cluster_ordering)
            preds[t_idx, :] = pred_t
            scores[t_idx, :] = scores_t
        else:
            raise FileNotFoundError(f"StrainGST output for t_idx={t_idx} not found. (path={t_path})")

    # renormalize.
    preds = preds / preds.sum(axis=-1, keepdims=True)

    runtime = 0
    for t_idx in range(len(time_points)):
        runtime += parse_runtime(output_dir / f'runtime.{t_idx}.txt')
    return preds, scores, cluster_ordering, cluster_df, runtime


def parse_straingst_pred_single(pred_file: Path, cluster_ordering: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    abund_t = np.zeros(len(cluster_ordering), dtype=float)
    score_t = np.zeros(len(cluster_ordering), dtype=float)
    clust_to_idx = {s: i for i, s in enumerate(cluster_ordering)}

    df = pd.read_csv(pred_file, sep='\t')
    for _, row in df.iterrows():
        acc = row['strain']
        rapct = float(row['rapct'])
        score = float(row['score'])
        abund_t[clust_to_idx[acc]] = rapct * 100.0
        score_t[clust_to_idx[acc]] = score
    return abund_t, score_t


def load_straingst_cluster(straingst_cluster_path: Path, phylogroup_path: Path) -> pd.DataFrame:
    phylogroups = parse_phylogroups(phylogroup_path)
    df_entries = []
    with open(straingst_cluster_path, "rt") as f:
        for line in f:
            clust = line.strip().split('\t')
            rep = clust[0]
            for member in clust:
                df_entries.append({
                    'Accession': member,
                    'Cluster': rep,
                    'ClusterPhylogroup': phylogroups[rep]
                })
    return pd.DataFrame(df_entries)


def straingst_subset_prediction(
        truth_accs: List[str],
        ground_truth: np.ndarray,
        pred: np.ndarray,
        scores: np.ndarray,
        pred_ordering: Dict[str, int],
        clust_subset: List[str],
        straingst_clust_df: pd.DataFrame
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_timepoints = pred.shape[0]
    clust_indices = {c: i for i, c in enumerate(clust_subset)}  # phylogroup A only
    SUBSET_pred = np.zeros((n_timepoints, len(clust_subset)), dtype=float)
    SUBSET_scores = np.zeros((n_timepoints, len(clust_subset)), dtype=float)
    SUBSET_truth = np.zeros((n_timepoints, len(clust_subset)), dtype=float)
    SUBSET_true_labels = np.full(len(clust_subset), dtype=bool, fill_value=False)

    # Populate the abundances.
    for tgt_idx, tgt_clust in enumerate(clust_subset):
        pred_idx = pred_ordering[tgt_clust]
        SUBSET_pred[:, tgt_idx] = pred[:, pred_idx]
        SUBSET_scores[:, tgt_idx] = scores[:, pred_idx]

    # Create the matching ground-truth clustered abundance.
    for sim_index, sim_acc in enumerate(truth_accs):
        cluster_id = straingst_clust_df.loc[straingst_clust_df['Accession'] == sim_acc, 'Cluster'].item()
        tgt_idx = clust_indices[cluster_id]  # this will throw an error if the cluster is not phylogroup A
        SUBSET_truth[:, tgt_idx] = ground_truth[:, sim_index]
        SUBSET_true_labels[tgt_idx] = True
    SUBSET_pred = SUBSET_pred / np.sum(SUBSET_pred, axis=-1, keepdims=True)
    return SUBSET_pred, SUBSET_scores, SUBSET_truth, SUBSET_true_labels


def straingst_results(
    data_dir: Path,
    mut_ratio: str, 
    replicate: int, 
    read_depth: int, 
    trial: int, 
    abundance_bins: np.ndarray,
    cluster_path: Path,
    phylogroup_path: Path,
    subdir_name: str = 'straingst'
):
    truth_accs, time_points, ground_truth = load_ground_truth(mut_ratio=mut_ratio, replicate=replicate, data_dir=data_dir)
    pred, scores, clusters, straingst_clust_df, runtime = extract_straingst_prediction(
        data_dir, mut_ratio, replicate, read_depth, trial, time_points,
        cluster_path=cluster_path,
        phylogroup_path=phylogroup_path,
        subdir_name=subdir_name
    )
    straingst_ordering = {c: i for i, c in enumerate(clusters)}

    """ Extract phylogroup A prediction/truth. """
    # First, check that the four target genomes are in distinct clusters.
    sim_clusts = straingst_clust_df.loc[straingst_clust_df['Accession'].isin(set(truth_accs)), 'Cluster']
    if len(truth_accs) != len(pd.unique(sim_clusts)):
        raise ValueError(
            "Resulting clustering does not separate the {} target accessions for replicate {}, read_depth {}, trial {}".format(
                len(truth_accs), replicate, read_depth, trial))

    # Next initialize the ground truth/prediction matrices.
    phylogroup_A_clusts = list(pd.unique(straingst_clust_df.loc[straingst_clust_df['ClusterPhylogroup'] == 'A', 'Cluster']))
    A_pred, A_scores, A_truth, A_true_indicators = straingst_subset_prediction(
        truth_accs, ground_truth,
        pred, scores, straingst_ordering,
        phylogroup_A_clusts, straingst_clust_df
    )

    # Simulated strains only
    sim_clusts = list(pd.unique(sim_clusts))
    sim_pred, sim_scores, sim_truth, sim_true_indicators = straingst_subset_prediction(
        truth_accs, ground_truth,
        pred, scores, straingst_ordering,
        sim_clusts, straingst_clust_df
    )

    # ================ Metric evaluation
    auroc = sklearn.metrics.roc_auc_score(  # Abundance thresholding per timepoint
        y_true=np.tile(A_true_indicators, (len(time_points), 1)).flatten(),
        y_score=A_pred.flatten()
    )
    auroc_collapsed = sklearn.metrics.roc_auc_score(  # Abundance thresholding, collapsed
        y_true=A_true_indicators,
        y_score=np.max(A_pred, axis=0),
    )

    eps = 1e-4
    rms_error_sim = rms(np.log10(sim_pred + eps), np.log10(sim_truth + eps))
    rms_error_A = rms(np.log10(A_pred + eps), np.log10(A_truth + eps))

    tv_err_A = tv_error(A_pred, A_truth)
    tv_err_sim = tv_error(sim_pred, sim_truth)

    rank_corr_sim = compute_rank_corr(sim_pred, sim_truth)
    rank_corr_A = compute_rank_corr(A_pred, A_truth)

    binned_rms_error_sim = binned_rms(np.log10(sim_pred + eps), np.log10(sim_truth), abundance_bins)
    split_rms_sim = strain_split_rms(np.log10(sim_pred + eps), np.log10(sim_truth))

    # ================= Output
    return {
        'MutRatio': mut_ratio, 'Replicate': replicate, 'ReadDepth': read_depth, 'Trial': trial,
        'Method': 'StrainGST',
        'NumClusters': len(phylogroup_A_clusts),
        'TVErrorSim': tv_err_sim,
        'TVErrorA': tv_err_A,
        'RMSErrorSim': rms_error_sim,
        'RMSErrorA': rms_error_A,
        'AUROC': auroc,
        'AUROC_Collapsed': auroc_collapsed,
        'RankCorrelationSim': rank_corr_sim,
        'RankCorrelationA': rank_corr_A,
        'Runtime': runtime
    } | {
        f'RMSErrorSim_Bin{i}': binned_rms
        for i, binned_rms in enumerate(binned_rms_error_sim)
    } | {
        f'RMSErrorSim_Strain{i}': _rms
        for i, _rms in enumerate(split_rms_sim)
    }


def straingst_roc(
        data_dir: Path,
        mut_ratio: str, replicate: int, read_depth: int, trial: int,
        cluster_path: Path,
        phylogroup_path: Path,
) -> Tuple[np.ndarray, np.ndarray]:
    truth_accs, time_points, ground_truth = load_ground_truth(mut_ratio=mut_ratio, replicate=replicate, data_dir=data_dir)
    pred, scores, clusters, straingst_clust_df, runtime = extract_straingst_prediction(
        data_dir, mut_ratio, replicate, read_depth, trial, time_points,
        cluster_path=cluster_path,
        phylogroup_path=phylogroup_path
    )
    straingst_ordering = {c: i for i, c in enumerate(clusters)}

    """ Extract phylogroup A prediction/truth. """
    # First, check that the four target genomes are in distinct clusters.
    sim_clusts = straingst_clust_df.loc[straingst_clust_df['Accession'].isin(set(truth_accs)), 'Cluster']
    if len(truth_accs) != len(pd.unique(sim_clusts)):
        raise ValueError(
            "Resulting clustering does not separate the {} target accessions for replicate {}, read_depth {}, trial {}".format(
                len(truth_accs), replicate, read_depth, trial))

    # Next initialize the ground truth/prediction matrices.
    phylogroup_A_clusts = list(pd.unique(straingst_clust_df.loc[straingst_clust_df['ClusterPhylogroup'] == 'A', 'Cluster']))
    A_pred, A_scores, A_truth, A_true_indicators = straingst_subset_prediction(
        truth_accs, ground_truth,
        pred, scores, straingst_ordering,
        phylogroup_A_clusts, straingst_clust_df
    )

    fpr, tpr, thresholds = sklearn.metrics.roc_curve(  # Abundance thresholding, (TxS)
        y_true=np.tile(A_true_indicators, (len(time_points), 1)).flatten(),
        y_score=A_pred.flatten(),
    )
    # fpr, tpr, thresholds = sklearn.metrics.roc_curve(  # Abundance thresholding
    #     y_true=A_true_indicators,
    #     y_score=np.max(A_pred, axis=0),
    # )
    return fpr, tpr
