import argparse
import os
import re
import sys

import pandas as pd

from .. import config
from ..helpers import aws
from ..helpers.helpers import timer
from .cleaners import cleaner_funcs
from .selectors import selector_funcs, sample_counts
from .creators import creator_funcs
from .selection_table import selection_table, write_selection_table


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_path')
    parser.add_argument('output_path')
    return parser.parse_args()


@timer
def read_data(path):
    return aws.read_parquet(path)


@timer
def clean_data(df):
    for func in cleaner_funcs:
        df = func(df)
    return df


@timer
def select_data(df):
    for func in selector_funcs:
        df = func.func(df, **func.kwargs)
    return df


@timer
def create_vars(df):
    if not df.empty:
        for func in creator_funcs:
            df = func(df)
    return df


@timer
def write_data(df, path, **kwargs):
    aws.write_parquet(df, path, **kwargs)
    return df


def _get_sample_name(path):
    sample_name_pattern = '[X\d]+'
    filename = os.path.basename(path)
    return re.search(sample_name_pattern, filename).group()


def main(input_path, output_path):
    sample_name = _get_sample_name(input_path)
    print('Sample:', sample_name)
    df = (read_data(input_path)
          .pipe(clean_data)
          .pipe(select_data)
          .pipe(create_vars)
          .pipe(write_data, output_path, verbose=True))

    table = selection_table(sample_counts)
    table_name = f'sample_selection_{sample_name}.tex'
    table_path = os.path.join(config.TABDIR, table_name)
    write_selection_table(table, table_path)
    with pd.option_context('max_colwidth', 25):
        print(table)


if __name__ == "__main__":
    args = parse_args(sys.argv)
    main(args.input_path, args.output_path)

