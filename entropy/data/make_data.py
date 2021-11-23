import argparse
import os
import re
import sys

import pandas as pd

from entropy import config
from entropy.helpers import aws
from entropy.helpers import helpers
from .cleaners import cleaner_funcs
from .selectors import selector_funcs, sample_counts
from .creators import creator_funcs
from .validators import validator_funcs
from .selection_table import selection_table, write_selection_table


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")
    parser.add_argument("output_path")
    return parser.parse_args(argv)


def read_data(path):
    return aws.read_parquet(path)


def clean_data(df):
    for func in cleaner_funcs:
        df = func(df)
    return df


def select_sample(df):
    for func in selector_funcs:
        df = func.func(df, **func.kwargs)
    return df


def create_vars(df):
    if not df.empty:
        for func in creator_funcs:
            df = func(df)
    return df


def validate_data(df):
    for func in validator_funcs:
        df = func(df)
    return df


def write_data(df, path, **kwargs):
    aws.write_parquet(df, path, **kwargs)
    return df


def get_sample_name(path):
    sample_name_pattern = "[X\d]+"
    filename = os.path.basename(path)
    return re.search(sample_name_pattern, filename).group()


def get_table_path(sample_name):
    table_name = f"sample_selection_{sample_name}.tex"
    return os.path.join(config.TABDIR, table_name)


@helpers.timer
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    sample_name = get_sample_name(args.input_path)
    print("Making sample:", sample_name)

    df = (
        read_data(args.input_path)
        .pipe(clean_data)
        .pipe(select_sample)
        .pipe(create_vars)
        .pipe(validate_data)
        .pipe(write_data, args.output_path, verbose=True)
    )

    table = selection_table(sample_counts)
    tbl_path = get_table_path(sample_name)
    write_selection_table(table, tbl_path)
    with pd.option_context('max_colwidth', 25):
        print(table)


if __name__ == "__main__":
    main()
