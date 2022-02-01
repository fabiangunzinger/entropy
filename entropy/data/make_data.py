import argparse
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
    return parser.parse_args(argv)


@hh.timer
def clean_data(df):
    for func in cl.cleaner_funcs:
        df = func(df)
    return df


@hh.timer
def select_sample(df):
    for func in sl.selector_funcs:
        df = func(df)
    return df


@hh.timer
def validate_data(df):
    for func in vl.validator_funcs:
        func(df)
    return df


def aggregate_data(df):
    return pd.concat((func(df) for func in agg.aggregator_funcs), axis=1, join="outer")


@hh.timer
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    print("Making sample:", args.sample)

    txn_path = os.path.join(config.AWS_BUCKET, f"txn_{args.sample}.parquet")
    analysis_path = os.path.join(config.AWS_BUCKET, f"analysis_{args.sample}.parquet")

    df = (
        hd.read_raw_data(args.sample)
        .pipe(clean_data)
        .pipe(ha.write_parquet, txn_path)
        .pipe(aggregate_data)
        .pipe(select_sample)
        .pipe(validate_data)
        .pipe(ha.write_parquet, analysis_path)
    )
    print(df.head())

    selection_table = st.make_selection_table(sl.sample_counts)
    st.write_selection_table(selection_table, args.sample)
    with pd.option_context("max_colwidth", 25):
        print(selection_table)


if __name__ == "__main__":
    main()
