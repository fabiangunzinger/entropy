"""
Produces transactions and analysis data for entropy project.

Analysis data is produced from transactions data, which is produced from raw
data. Because analysis data is being changed as the analysis progresses while the
underlying transactions data tends to remain unchanged and takes much longer to
process, the program by default starts the processing from the txns data. But
the `--from-raw` option can be passed to first create new transactions data.

"""


import argparse
import functools
import os
import sys

import pandas as pd

from entropy import config
import entropy.data.aggregators as agg
import entropy.data.cleaners as cl
import entropy.data.selection_table as st
import entropy.data.selectors as sl
import entropy.data.validators as vl
import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.helpers.helpers as hh


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("sample")
    parser.add_argument("--from-raw", action="store_true", help="start from raw data")
    return parser.parse_args(argv)


@hh.timer
def read_raw_data(sample):
    return hd.read_raw_data(sample)


@hh.timer
def clean_data(df):
    return functools.reduce(lambda df, f: f(df), cl.cleaner_funcs, df)


@hh.timer
def select_sample(df):
    return functools.reduce(lambda df, f: f(df), sl.selector_funcs, df)


@hh.timer
def validate_data(df):
    return functools.reduce(lambda df, f: f(df), vl.validator_funcs, df)


@hh.timer
def aggregate_data(df):
    """Concats all columns."""
    return pd.concat(
        (func(df) for func in agg.aggregator_funcs), axis=1, join="inner"
    ).reset_index()


@hh.timer
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    if args.from_raw:
        raw_data = read_raw_data(args.sample)
        txn_data = clean_data(raw_data)
        fp = os.path.join(config.AWS_BUCKET, f"txn_{args.sample}.parquet")
        ha.write_parquet(txn_data, fp)
    else:
        txn_data = hd.read_txn_data(args.sample)

    agg_data = aggregate_data(txn_data)
    analysis_data = select_sample(agg_data)
    fp = os.path.join(config.AWS_BUCKET, f"analysis_{args.sample}.parquet")
    ha.write_parquet(analysis_data, fp)
    validate_data(analysis_data)

    selection_table = st.make_selection_table(sl.sample_counts)
    st.write_selection_table(selection_table, args.sample)
    with pd.option_context("max_colwidth", 25):
        print(selection_table)


if __name__ == "__main__":
    main()
