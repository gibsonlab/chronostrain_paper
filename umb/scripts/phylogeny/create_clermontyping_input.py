import argparse
import math
from pathlib import Path
from typing import List

import pandas as pd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create bash script wrapper for clermonTyping.sh."
    )

    # Input specification.
    parser.add_argument('-i', '--refseq_index', required=True, type=str,
                        help='<Required> The path to the refseq index file generated by init_chronostrain.sh.')
    parser.add_argument('-c', '--clermon_script_path', required=True, type=str,
                        help='<Required> The path to clermonTyping.sh')
    parser.add_argument('-o', '--output_path', required=True, type=str,
                        help='<Required> The target output path to write the resulting wrapper script to.')

    parser.add_argument('-a', '--analysis_name', required=False, type=str,
                        default='umb',
                        help='<Optional> The name of the analysis to pass to clermonTyping. (default: `umb`)')
    return parser.parse_args()


def bash_escape(x: str) -> str:
    return x.replace('(', '\\(').replace(')', '\\)').replace('\'', '\\\'')


def fasta_batches(paths: List[Path], batch_sz: int) -> List[List[Path]]:
    batches = []

    n_batches = math.ceil(len(paths) / batch_sz)
    for batch_idx in range(n_batches):
        start = int(batch_idx * batch_sz)
        end = int(min((batch_idx + 1) * batch_sz, len(paths)))
        batches.append(paths[start:end])

    return batches


def main():
    args = parse_args()
    seq_batch_size = 100
    script = "bash {clermon_script_path} --fasta {fasta_path} --name {analysis_name}_{batch_idx}"

    df = pd.read_csv(args.refseq_index, sep='\t')
    fasta_paths = []
    for idx, row in df.loc[df['Genus'] == 'Escherichia', :].iterrows():
        fasta_paths.append(row['SeqPath'])

    output_path = Path(args.output_path)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_path, 'w') as f:
        for batch_idx, fasta_batch in enumerate(fasta_batches(fasta_paths, seq_batch_size)):
            print(
                script.format(
                    clermon_script_path=args.clermon_script_path,
                    fasta_path='@'.join(bash_escape(str(p)) for p in fasta_batch),
                    analysis_name=args.analysis_name,
                    batch_idx=batch_idx
                ),
                file=f
            )

    print(f"Wrote script wrapper to {args.output_path}")


if __name__ == "__main__":
    main()
