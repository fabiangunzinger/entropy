"""
Produces analysis dataset.

"""

import argparse
import collections
import concurrent
import functools
import os
import sys

import pandas as pd

import src.config as config
import src.data.aggregators as agg
import src.data.selectors as sl
import src.data.transformers as tf
import src.data.validators as vl
import src.helpers.data as hd
import src.helpers.helpers as hh
import src.helpers.io as io


TIMER_ON = True


@hh.timer(on=TIMER_ON)
def read_piece(filepath, **kwargs):
    print("Reading", filepath)
    return io.read_parquet(filepath, **kwargs)


@hh.timer(on=TIMER_ON)
def aggregate_data(df):
    return pd.concat((f(df) for f in agg.aggregators), axis=1).reset_index()


@hh.timer(on=TIMER_ON)
def select_sample(df):
    return functools.reduce(lambda df, f: f(df), sl.selectors, df)


@hh.timer(on=TIMER_ON)
def clean_piece(filepath):
    return read_piece(filepath).pipe(aggregate_data).pipe(select_sample)


@hh.timer(on=TIMER_ON)
def transform_variables(df):
    return functools.reduce(lambda df, f: f(df), tf.transformers, df)


@hh.timer(on=TIMER_ON)
def validate_data(df):
    return functools.reduce(lambda df, f: f(df), vl.validators, df)


def get_filepath(piece):
    return os.path.join(config.AWS_PIECES, f"mdb_XX{piece}.parquet")


def write_data(df, piece, label, debug=False):
    id = ""
    if piece:
        id += f"_XX{piece}"
    if label:
        id += f"_{label}"
    if debug:
        id += "_debug"
    fn = "entropy" + id + ".parquet"
    fp = os.path.join(config.AWS_PROJECT, fn)
    io.write_parquet(df, fp)
    return df


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--piece", help="Piece in [0,9] to process")
    parser.add_argument("-l", "--label", help="Label to add to filename")
    return parser.parse_args(args)


@hh.timer(on=TIMER_ON)
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    # Use supplied test piece or all pieces and name datafile accordingly
    pieces = args.piece if args.piece else range(10)
    pieces_paths = [get_filepath(piece) for piece in pieces]

    data = (
        pd.concat(clean_piece(path) for path in pieces_paths)
        .reset_index(drop=True)
        .pipe(transform_variables)
        .pipe(write_data, args.piece, args.label, debug=True)
        .pipe(validate_data)
        .pipe(write_data, args.piece, args.label)
    )

    selection_table = hd.make_selection_table(sl.sample_counts)
    table_path = os.path.join(config.TABDIR, "sample_selection.tex")
    hd.write_selection_table(selection_table, table_path)

    with pd.option_context("max_colwidth", 25):
        print(selection_table)


if __name__ == "__main__":
    main()
