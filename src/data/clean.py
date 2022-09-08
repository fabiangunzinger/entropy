"""
This program reads in raw data pieces and produces minimally cleaned pieces
that can be stored and read efficiently and be used as the basis for all
research projects.

"""

import argparse
import functools
import os
import re
import sys
import time

import numpy as np
import pandas as pd

import src.config as config
import src.txn_classifications as tc
import src.io as io


cleaner_funcs = []


def cleaner(func):
    """Adds function to list of cleaner functions."""
    cleaner_funcs.append(func)
    return func


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        diff = end - start
        unit = "seconds"
        if diff > 60:
            diff = diff / 60
            unit = "minutes"
        print(f"Time for {func.__name__:30}: {diff:.2f} {unit}")
        return result

    return wrapper


@cleaner
@timer
def remove_header_dots(df):
    """Restores original variable names."""
    return df.rename(columns=lambda x: x.replace(".", " "))


@cleaner
@timer
def cast_dtypes(df):
    """Converts columns to storage-efficient types."""

    dtypes = {
        "Transaction Reference": "int32",
        "User Reference": "int32",
        "Year of Birth": "float32",
        "Salary Range": "category",
        "Postcode": "category",
        "LSOA": "category",
        "MSOA": "category",
        "Derived Gender": "category",
        "Account Reference": "int32",
        "Provider Group Name": "category",
        "Account Type": "category",
        "Latest Recorded Balance": "float32",
        "Transaction Description": "category",
        "Credit Debit": "category",
        "Amount": "float32",
        "User Precedence Tag Name": "category",
        "Manual Tag Name": "category",
        "Auto Purpose Tag Name": "category",
        "Merchant Name": "category",
        "Merchant Business Line": "category",
        "Transaction Updated Flag": "category",
        "User Registration Date": "datetime64",
        "Transaction Date": "datetime64",
        "Account Created Date": "datetime64",
        "Account Last Refreshed": "datetime64",
        "Data Warehouse Date Last Updated": "datetime64",
        "Data Warehouse Date Created": "datetime64",
    }

    for var, dtype in dtypes.items():
        df[var] = df[var].astype(dtype)
    return df


@cleaner
@timer
def rename_cols(df):
    """Renames excessively long columns for more convenient typing."""
    new_names = {
        "Account Created Date": "account_created",
        "Account Reference": "account_id",
        "Derived Gender": "gender",
        "Merchant Name": "merchant",
        "Postcode": "postcode",
        "Provider Group Name": "account_provider",
        "Salary Range": "salary_range",
        "Transaction Date": "date",
        "Transaction Description": "desc",
        "Transaction Reference": "id",
        "Transaction Updated Flag": "updated_flag",
        "User Reference": "user_id",
        "Year of Birth": "birth_year",
        "Auto Purpose Tag Name": "tag_auto",
        "Manual Tag Name": "tag_manual",
        "User Precedence Tag Name": "tag_up",
        "Latest Recorded Balance": "latest_balance",
    }
    return df.rename(columns=new_names)


@cleaner
@timer
def clean_headers(df):
    """Converts column headers to snake case."""
    df.columns = (
        df.columns.str.lower().str.replace(r"[\s\.]", "_", regex=True).str.strip()
    )
    return df


@cleaner
@timer
def lowercase_categories(df):
    """Converts all category values to lowercase to simplify regex searches.

    Recasts categories because casting to lowercase can lead to duplicate
    categories.
    """
    cat_vars = df.select_dtypes("category").columns
    df[cat_vars] = df[cat_vars].apply(lambda x: x.str.lower()).astype("category")
    return df


@cleaner
@timer
def drop_missing_txn_desc(df):
    return df[df.desc.notna()]


@cleaner
@timer
def gender_to_female(df):
    """Replaces gender variable with female dummy.

    Uses float type becuase bool type doesn't handle na values well.
    """
    mapping = {"f": 1, "m": 0, "u": np.nan}
    df["is_female"] = df.gender.map(mapping).astype("float32")
    return df.drop(columns="gender")


@cleaner
@timer
def credit_debit_to_debit(df):
    """Replaces credit_debit variable with credit dummy."""
    df["is_debit"] = df.credit_debit.eq("debit")
    return df.drop(columns="credit_debit")


@cleaner
@timer
def sign_amount(df):
    """Makes credits negative."""
    df["amount"] = df.amount.where(df.is_debit, df.amount.mul(-1))
    return df


@cleaner
@timer
def missing_tags_to_nan(df):
    """Converts missing category values to NaN."""
    df["merchant"] = df["merchant"].cat.remove_categories(["no merchant"])
    df["merchant_business_line"] = df["merchant_business_line"].cat.remove_categories(
        ["no merchant business line", "unknown merchant"]
    )
    df["tag_auto"] = df["tag_auto"].cat.remove_categories(["no tag"])
    return df


@cleaner
@timer
def zero_balances_to_missing(df):
    """Replaces zero latest balances with missings.

    Latest balance column refers to account balance at last account
    refresh date. Exact zero values are likely due to unsuccessful
    account refresh (see data dictionary) and thus treated as missing.
    """
    df["latest_balance"] = df.latest_balance.replace(0, np.nan)
    return df


def _apply_grouping(df, col_name, grouping):
    """Applies grouping to col_name in dataframe in-place.

    Args:
      grouping: a dict with name-tags pairs, where name
        is the group name that will be applied to each txn
        for which tag_auto equals one of the tags.
      col_name: a column from df into which the group
        names will be stored.
    """
    for group, tags in grouping.items():
        escaped_tags = [re.escape(tag) for tag in tags]
        pattern = "|".join(escaped_tags)
        mask = df.tag_auto.str.fullmatch(pattern, na=False)
        df.loc[mask, col_name] = group

    return df


@cleaner
@timer
def add_tag(df):
    """Creates custom transaction tags for spends, income, and transfers."""
    df["tag"] = np.nan
    _apply_grouping(df, "tag", tc.spend_subgroups)
    _apply_grouping(df, "tag", tc.income_subgroups)
    _apply_grouping(df, "tag", tc.transfers_subgroups)
    df["tag"] = df.tag.astype("category")
    return df


@cleaner
@timer
def tag_corrections(df):
    """Fix issues with automatic tagging.

    Correction is applied to `tag` to leave `tag_auto`
    unchanged but to ensure that correction will be taken
    into account in `add_tag_group()` below.
    """
    # tag as tranfser those txns that are clear transfers
    # according to their description string but aren't tagged
    # as such
    tfr_strings = [" ft", " trf", "xfer", "transfer"]
    tfr_pattern = "|".join(tfr_strings)
    exclude_strings = ["fee", "interest", "rewards"]
    exclude_pattern = "|".join(exclude_strings)
    mask = (
        df.desc.str.contains(tfr_pattern)
        & df.desc.str.contains(exclude_pattern).eq(False)
        & df.tag.isna()
    )
    df.loc[mask, "tag"] = "other_transfers"

    # tag untagged txns as other_spend if desc contains "bbp",
    # which is short for bill payment
    mask = df.desc.str.contains("bbp") & df.tag.isna()
    df.loc[mask, "tag"] = "other_spend"

    # reclassify 'interest income' as finance spend if txn is a debit
    # as these are mostly overdraft fees
    mask = df.tag_auto.eq("interest income") & df.is_debit
    df.loc[mask, "tag"] = "finance"

    return df


@cleaner
@timer
def add_tag_group(df):
    """Groups transactions into income, spend, and transfers."""
    df["tag_group"] = np.nan
    _apply_grouping(df, "tag_group", tc.tag_groups)
    df["tag_group"] = df.tag_group.astype("category")
    return df


@cleaner
@timer
def add_tag_spend(df):
    """Create separate variable for corrected auto tag spend categories.

    Auto tag variable has duplicated categories such as 'bank charges' and
    'banking charges'.
    """
    df["tag_spend"] = np.nan
    _apply_grouping(df, "tag_spend", tc.tag_spend)
    df["tag_spend"] = df.tag_spend.astype("category")
    return df


@cleaner
@timer
def drop_duplicates(df):
    """Drops duplicate transactions.

    Retains only the first of all txns for which user_id, account_id,
    date, amount, and desc are identical.

    While this might drop some genuine duplicates (e.g. buying the same
    coffee at the same place on the same day), data inspection suggests
    that most dropped txns are unlikely to be genuine.
    """
    df = df.copy()
    cols = ["user_id", "account_id", "date", "amount", "desc"]
    return df.drop_duplicates(subset=cols)


@cleaner
@timer
def add_region(df):
    """Adds region name."""
    columns = ["pcsector", "region_name", "is_urban"]
    fp = "s3://3di-data-ons/nspl/NSPL_AUG_2020_UK/clean/lookup.csv"
    try:
        regions = io.read_csv(fp, usecols=columns).rename(
            columns={"pcsector": "postcode"}
        )
    except FileNotFoundError:
        print("NSPL lookup table not found.")

    return df.merge(regions, how="left", on="postcode", validate="m:1")


@cleaner
@timer
def is_sa_flow(df):
    """Dummy for whether txn is in- or outflow of savings account."""
    df["is_sa_flow"] = (
        df.account_type.eq("savings")
        & df.amount.abs().ge(5)
        & ~df.tag_auto.str.contains("interest", na=False)
        & ~df.desc.str.contains(r"save\s?the\s?change", na=False)
    )
    return df


@cleaner
@timer
def is_salary_pmt(df):
    """Dummy for whether txn is salary payment.

    Salaries are one possible source of income, as classified
    in txn_classifications.py.
    """
    df["is_salary_pmt"] = df.tag.eq('earnings') & ~df.is_debit
    return df


@cleaner
@timer
def is_income_pmt(df):
    """Dummy for whether txn is income payment."""
    df["is_income_pmt"] = df.tag_group.eq('income') & ~df.is_debit
    return df


@cleaner
@timer
def year_month_indicator(df):
    df["ym"] = df.date.dt.to_period("m")
    return df


@cleaner
@timer
def order_and_sort(df):
    """Orders columns and sort values."""
    cols = df.columns
    first = ["date", "user_id", "amount", "desc", "merchant", "tag_group", "tag_spend"]
    user = cols[cols.str.startswith("user") & ~cols.isin(first)]
    account = cols[cols.str.startswith("account") & ~cols.isin(first)]
    txn = cols[~cols.isin(user.append(account)) & ~cols.isin(first)]
    order = first + sorted(user) + sorted(account) + sorted(txn)
    return df[order].sort_values(["user_id", "date"])


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    return parser.parse_args(args)


def clean_path(path):
    """Returns path for cleaned raw piece.

    Raw pieces are stored in <bucket>/raw/pieces/<filename>,
    clean pieces in <bucket>/clean/pieces/<filename>.
    """
    return path.replace('/raw/', '/clean/')


@timer
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    df_raw = io.read_parquet(args.filepath)
    df_clean = functools.reduce(lambda df, f: f(df), cleaner_funcs, df_raw)
    fp_clean = clean_path(args.filepath)
    io.write_parquet(df_clean, fp_clean)


if __name__ == "__main__":
    main()
