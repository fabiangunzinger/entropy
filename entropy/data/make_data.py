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
    columns = [
        "Transaction Reference",
        "User Reference",
        "Year of Birth",
        "Postcode",
        "Derived Gender",
        "Transaction Date",
        "Account Reference",
        "Provider Group Name",
        "Account Type",
        "Transaction Description",
        "Credit Debit",
        "Amount",
        "Auto Purpose Tag Name",
        "Merchant Name",
        "Latest Recorded Balance",
        "Account Last Refreshed",
    ]
    return hd.read_raw_data(sample, columns=columns)


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
    """Concats all columns and orders columns to R plm standard."""
    data = (
        pd.concat((func(df) for func in agg.aggregator_funcs), axis=1, join="outer")
        .reset_index()
        .assign(month=lambda df: df.date.dt.month)
    )
    return hd.order_columns(data, first=['user_id', 'month', 'date'])



@hh.timer
def write_data(df, filename, **kwargs):
    filepath = os.path.join(config.AWS_BUCKET, filename)
    ha.write_parquet(df, filepath, **kwargs)
    return df


@hh.timer
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)

    df = (
        (
            read_raw_data(args.sample)
            .pipe(clean_data)
            .pipe(write_data, f"txn_{args.sample}.parquet")
            if args.from_raw
            else hd.read_txn_data(args.sample)
        )
        .pipe(aggregate_data)
        .pipe(select_sample)
        .pipe(write_data, f"analysis_{args.sample}.parquet", index=True)
        .pipe(validate_data)
    )

    selection_table = st.make_selection_table(sl.sample_counts)
    st.write_selection_table(selection_table, args.sample)
    with pd.option_context("max_colwidth", 25):
        print(selection_table)


if __name__ == "__main__":
    main()
