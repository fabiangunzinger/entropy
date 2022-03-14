"""
Functions to clean raw MDB transaction data.

"""

import os
import re
import string

import numpy as np
import pandas as pd

from entropy import config
import entropy.data.txn_classifications as tc
import entropy.helpers.aws as ha
import entropy.helpers.helpers as hh


cleaner_funcs = []


def cleaner(func):
    """Adds function to list of cleaner functions."""
    cleaner_funcs.append(func)
    return func


@cleaner
@hh.timer
def rename_cols(df):
    """Renames columns where needed.

    Each variable in the data pertains either to a txn, a user,
    or an account, and is prepended by an appropriate prefix,
    except, for brevity, txn variables, which have no prefix
    (e.g `txn_id` is `id`).
    """
    new_names = {
        # "Account Created Date": "account_created",
        "Account Reference": "account_id",
        "Derived Gender": "gender",
        # "LSOA": "lsoa",
        # "MSOA": "msoa",
        "Merchant Name": "merchant",
        "Postcode": "postcode",
        "Provider Group Name": "account_provider",
        # "Salary Range": "salary_range",
        "Transaction Date": "date",
        "Transaction Description": "desc",
        "Transaction Reference": "id",
        # "Transaction Updated Flag": "updated_flag",
        "User Reference": "user_id",
        "Year of Birth": "yob",
        "Auto Purpose Tag Name": "tag_auto",
        # "Manual Tag Name": "tag_manual",
        # "User Precedence Tag Name": "tag_up",
        "Latest Recorded Balance": "latest_balance",
    }
    return df.rename(columns=new_names)


@cleaner
@hh.timer
def clean_headers(df):
    """Converts column headers to snake case."""
    df.columns = (
        df.columns.str.lower().str.replace(r"[\s\.]", "_", regex=True).str.strip()
    )
    return df


@cleaner
@hh.timer
def drop_first_and_last_month(df):
    """Drops first and last month for each user.

    These months have incomplete data for users who joined and left MDB during
    the month, which would bias monthly entropy scores downwards (if we only
    observe a single txn, entropy would be 0).
    """
    ym = df.date.dt.to_period("m")
    first_month = ym.groupby(df.user_id).transform("min")
    last_month = ym.groupby(df.user_id).transform("max")
    return df[ym.between(first_month, last_month, inclusive="neither")]


@cleaner
@hh.timer
def lowercase_categories(df):
    """Converts all category values to lowercase to simplify regex searches.

    Recasts categories because casting to lowercase can lead to duplicate
    categories.
    """
    cat_vars = df.select_dtypes("category").columns
    df[cat_vars] = df[cat_vars].apply(lambda x: x.str.lower()).astype("category")
    return df


@cleaner
@hh.timer
def drop_missing_txn_desc(df):
    return df[df.desc.notna()]


@cleaner
@hh.timer
def gender_to_female(df):
    """Replaces gender variable with female dummy.

    Uses float type becuase bool type doesn't handle na values well.
    """
    mapping = {"f": 1, "m": 0, "u": np.nan}
    df["female"] = df.gender.map(mapping).astype("float32")
    return df.drop(columns="gender")


@cleaner
@hh.timer
def credit_debit_to_debit(df):
    """Replaces credit_debit variable with credit dummy."""
    df["debit"] = df.credit_debit.eq("debit")
    return df.drop(columns="credit_debit")


@cleaner
@hh.timer
def sign_amount(df):
    """Makes credits negative."""
    df["amount"] = df.amount.where(df.debit, df.amount.mul(-1))
    return df


@cleaner
@hh.timer
def missing_tags_to_nan(df):
    """Converts missing category values to NaN."""
    df["merchant"] = df["merchant"].cat.remove_categories(["no merchant"])
    df["tag_auto"] = df["tag_auto"].cat.remove_categories(["no tag"])
    return df


@cleaner
@hh.timer
def zero_balances_to_missing(df):
    """Replaces zero latest balances with missings.

    Latest balance column refers to account balance at last account
    refresh date. Exact zero values are likely due to unsuccessful
    account refresh (see data dictionary) and thus treated as missing.
    """
    df["latest_balance"] = df.latest_balance.replace(0, np.nan)
    return df


def _apply_grouping(grouping, df, col_name):
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
@hh.timer
def add_tag(df):
    """Creates custom transaction tags for spends, income, and transfers."""
    df["tag"] = np.nan
    _apply_grouping(tc.spend_subgroups, df, "tag")
    _apply_grouping(tc.income_subgroups, df, "tag")
    _apply_grouping(tc.transfers_subgroups, df, "tag")
    df["tag"] = df.tag.astype("category")
    return df


@cleaner
@hh.timer
def tag_corrections(df):
    """Fix issues with automatic tagging.

    Correction is applied to `tag` to leave `tag_auto`
    unchanged but to ensure that correction will be taken
    into account in `add_tag_group()` below.
    """
    # tag untagged as transfer if desc clearly indicates as much
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

    # tag untagged as other_spend if desc contains "bbp",
    # which is short for bill payment
    mask = df.desc.str.contains("bbp") & df.tag.isna()
    df.loc[mask, "tag"] = "other_spend"

    # reclassify 'interest income' as finance spend if txn is a debit
    # these are mostly overdraft fees
    mask = df.tag_auto.eq("interest income") & df.debit
    df.loc[mask, "tag"] = "finance"

    return df


@cleaner
@hh.timer
def add_tag_group(df):
    """Groups transactions into income, spend, and transfers."""
    df["tag_group"] = np.nan
    _apply_grouping(tc.tag_groups, df, "tag_group")
    df["tag_group"] = df.tag_group.astype("category")
    return df


@cleaner
@hh.timer
def drop_duplicates(df):
    """Drops duplicate transactions.

    Retains only the first of all txns for which user_id, account_id,
    date, amount, and desc are identical.
    """
    df = df.copy()
    cols = ["user_id", "account_id", "date", "amount", "desc"]
    return df.drop_duplicates(subset=cols)


@cleaner
@hh.timer
def add_logins(df, **kwargs):
    """Adds number of daily logins."""

    def read_daily_logins(**kwargs):
        fp = "s3://3di-data-mdb/raw/20200630_UserLoginsForNeedham.csv"
        df = ha.read_csv(fp, names=["user_id", "date"], parse_dates=["date"], **kwargs)
        df["date"] = df.date.dt.round("d")
        df["logins"] = 1
        return df.groupby(["user_id", "date"]).logins.sum().reset_index()

    logins = read_daily_logins(**kwargs)
    df = df.merge(logins, on=["user_id", "date"], how="left", validate="m:1")
    df["logins"] = df.logins.fillna(0)
    return df


@cleaner
@hh.timer
def add_region(df):
    """Adds region name."""
    columns = ["pcsector", "region_name", "is_urban"]
    fp = "s3://3di-data-ons/nspl/NSPL_AUG_2020_UK/clean/lookup.csv"
    try:
        regions = ha.read_csv(fp, usecols=columns).rename(
            columns={"pcsector": "postcode"}
        )
    except FileNotFoundError:
        print("NSPL lookup table not found.")

    return df.merge(regions, how="left", on="postcode", validate="m:1")


@cleaner
@hh.timer
def is_sa_flow(df):
    """Dummy for whether txn is in- or outflow of savings account."""
    is_sa_flow = (
        df.account_type.eq("savings")
        & df.amount.abs().ge(5)
        & ~df.tag_auto.str.contains("interest", na=False)
        & ~df.desc.str.contains(r"save\s?the\s?change", na=False)
    )
    df["is_sa_flow"] = is_sa_flow.astype(int)
    return df


@cleaner
@hh.timer
def is_salary_pmt(df):
    """Dummy for whether txn is salary payment."""
    df["is_salary_pmt"] = df.tag_auto.str.contains("salary") & ~df.debit
    return df


@cleaner
@hh.timer
def year_month_indicator(df):
    df["ym"] = df.date.dt.to_period("m")
    return df


@cleaner
@hh.timer
def order_and_sort(df):
    """Orders columns and sort values."""
    cols = df.columns
    first = ["date", "user_id", "amount", "desc", "merchant", "tag_group", "tag"]
    user = cols[cols.str.startswith("user") & ~cols.isin(first)]
    account = cols[cols.str.startswith("account") & ~cols.isin(first)]
    txn = cols[~cols.isin(user.append(account)) & ~cols.isin(first)]
    order = first + sorted(user) + sorted(account) + sorted(txn)

    return df[order].sort_values(["user_id", "date"])
