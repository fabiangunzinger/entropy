import argparse
from functools import wraps
import os
import re
import sys
import time

import pandas as pd

from .. import config
from ..helpers import aws
from .cleaners import cleaner_funcs
from .selectors import selector_funcs, sample_counts
from .selection_table import selection_table, write_selection_table


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        diff = end - start
        unit = 'seconds'
        if diff > 60:
            diff = diff / 60
            unit = 'minutes'
        print(f'Time for {func.__name__:12}: {diff:.2f} {unit}')
        return result
    return wrapper


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
        df = func(df)
    return df


@timer
def write_data(df, path):
    aws.write_parquet(df, path)
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
          .pipe(write_data, output_path))

    table = selection_table(sample_counts)
    table_name = f'sample_selection_{sample_name}.tex'
    table_path = os.path.join(config.TABDIR, table_name)
    write_selection_table(table, table_path)
    print(table)


if __name__ == "__main__":
    args = parse_args(sys.argv)
    main(args.input_path, args.output_path)

