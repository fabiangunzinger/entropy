"""
Create summary statistics table.

"""
import contextlib
import os

import tabulate

import entropy.helpers.data as hd
from entropy import config


def make_sumstats_table(df):
    """Creats basic summary statistics table for colums."""
    order = ["count", "mean", "std", "min", "max", "25%", "50%", "75%"]
    return df.describe().T[order]


def make_latex_sumstats_table(sumstats_table):
    return tabulate.tabulate(sumstats_table, headers="keys", tablefmt="latex_booktabs")


def write_table(table, path):
    """Writes table to path."""
    with open(path, "w+") as f:
        with contextlib.redirect_stdout(f):
            print(table)
    print(f"Table written to {path}.")


def main(df, write=True):
    sumstats_table = make_sumstats_table(df)
    if write: 
        latex_sumstats_table = make_latex_sumstats_table(sumstats_table)
        fp = os.path.join(config.TABDIR, "sumstats.tex")
        write_table(latex_sumstats_table, fp)
    return sumstats_table
    

if __name__ == '__main__':
    df = hd.read_analysis_data()
    main(df)
