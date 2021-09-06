import argparse
import sys
import pandas as pd
from ..helpers import aws
from .cleaners import cleaner_funcs
from .selectors import selector_funcs



def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('input_path')
    parser.add_argument('output_path')
    return parser.parse_args()


def clean_df(piece):
    """Clean a single piece."""
    df = aws.s3read_parquet(piece)
    for func in cleaner_funcs + selector_funcs:
        df = func(df)
    print(df.columns)
    print(df.head())
    print(df.info())
    return df



if __name__ == "__main__":
    args = parse_args(sys.argv)
    clean_df(args.input_path)
    print(args.input_path, args.output_path)
