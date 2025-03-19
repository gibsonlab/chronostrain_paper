import click
from pathlib import Path
import pickle

from chronostrain.model.io import TimeSeriesReads
from chronostrain.config import cfg
from chronostrain.algs.subroutines.cache import ReadsPopulationCache
from chronostrain.model.fragments import UnallocatedFragmentSpace

from chronostrain.logging import create_logger
logger = create_logger("chronostrain.fix_cache")


@click.command()
@click.option(
    '--reads', '-r', 'reads_input',
    type=click.Path(path_type=Path, dir_okay=False, exists=True, readable=True),
    required=True,
    help="Path to the reads input CSV file."
)
def main(
        reads_input: Path
):
    # ============ Create database instance.
    db = cfg.database_cfg.get_database()
    reads = TimeSeriesReads.load_from_csv(reads_input)
    if len(reads.time_slices) == 0:
        print("Input has no reads. Exiting.")
        return

    cache = ReadsPopulationCache(reads, db)

    target_cache_dir = cache.cache_dir
    if len(list(target_cache_dir.glob("fragments.fasta"))) > 0:
        logger.info("Target cache dir is already populated.")
    else:
        for subdir in target_cache_dir.parent.iterdir():
            if not subdir.is_dir():
                continue
            if subdir.name == target_cache_dir.name:
                continue

            logger.info("Found subdir {}, merging into {}".format(
                subdir.name, target_cache_dir.name
            ))

            if len(list(subdir.glob("fragment_frequencies"))) > 0:
                print("\tFound frag freq cache")
                freq_dir = subdir / "fragment_frequencies"
                assert freq_dir.is_dir()
                freq_dir.rename(target_cache_dir / "fragment_frequencies")

            elif len(list(subdir.glob("sparse_log_likelihoods_*.*"))) > 0:
                print("\tFound log likelihoods cache")
                target_subdir = target_cache_dir / 'log_likelihoods'
                target_subdir.mkdir(exist_ok=True, parents=False)
                for f in subdir.glob("sparse_log_likelihoods_*.*"):
                    f.rename(target_subdir / f.name)

            elif len(list(subdir.glob("fragments.fasta"))) > 0:
                print("\tFound fragments/alignments cache")
                f = subdir / "fragments.fasta"
                f.rename(target_cache_dir / "fragments.fasta")

                f = subdir / "fragments.fasta.cidx"
                f.rename(target_cache_dir / "fragments.fasta.cidx")

                f = subdir / "inference_fragments_dynamic.pkl"
                f.rename(target_cache_dir / "inference_fragments_dynamic.pkl")

                f = subdir / "alignments"
                f.rename(target_cache_dir / "alignments")
            else:
                print("\tUnknown cache type {}".format(subdir))

    # Validate fragment pickle.
    logger.info("Validating fragmentspace object.")
    with open(target_cache_dir / "inference_fragments_dynamic.pkl", "rb") as f:
        fragments: UnallocatedFragmentSpace = pickle.load(f)

    if fragments.fasta_resource.fasta_path.exists():
        logger.info("All good!")
        pass  # all good
    else:
        fragments = UnallocatedFragmentSpace(target_cache_dir / "fragments.fasta")
        with open(target_cache_dir / "inference_fragments_dynamic.pkl", "wb") as f:
            pickle.dump(fragments, f)
        logger.info("Rewrote pickle file to point to new file.")



if __name__ == "__main__":
    main()