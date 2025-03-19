from pathlib import Path
import pandas as pd
from Bio import SeqIO


def main():
    df_entries = []
    asm_dir = Path("assemblies").resolve()

    suffix = ".contigs_velvet.fa"
    print(f"Looking in {asm_dir}/*{suffix}")
    for asm_file in asm_dir.glob("*{}".format(suffix)):
        assert asm_file.name.endswith(suffix)
        asm_id = asm_file.name[:-len(suffix)]

        total_num_bases = sum(len(record.seq) for record in SeqIO.parse(asm_file, 'fasta'))
        
        df_entries.append({
            'Genus': 'Enterococcus',
            'Species': 'faecalis',
            'Strain': asm_id,
            'Accession': asm_id,
            'Assembly': asm_id,
            'SeqPath': asm_file,
            'ChromosomeLen': total_num_bases,
            'GFF': 'None'
        })
    df = pd.DataFrame(df_entries)
    df.to_csv("index.tsv", index=False, sep='\t')
    

if __name__ == "__main__":
    main()
