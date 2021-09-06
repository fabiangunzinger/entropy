import argparse
import os
import re
import sys

import pandas as pd

from .. import config
from ..helpers import aws
from .cleaners import cleaner_funcs
from .selectors import selector_funcs, sample_counts
from .selection_table import selection_table, write_selection_table


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_path')
    parser.add_argument('output_path')
    return parser.parse_args()


def clean_data(path):
    df = aws.s3read_parquet(path)
    for func in cleaner_funcs + selector_funcs:
        df = func(df)
    return df


def get_sample_name(path):
    sample_name_pattern = '[X\d]+'
    filename = os.path.basename(path)
    return re.search(sample_name_pattern, filename).group()


def main(input_path):
    df = clean_data(input_path)
    table = selection_table(sample_counts)

    sample_name = get_sample_name(input_path)
    tbl_name = f'sample_selection_{sample_name}.tex'
    tbl_path = os.path.join(config.TABDIR, tbl_name)
    write_selection_table(table, tbl_path)

    # print(selection_table)
    # print(input_path)
    # print(df.columns)
    # print(df.head())
    # print(df.info())


if __name__ == "__main__":

    args = parse_args(sys.argv)

    main(args.input_path)
