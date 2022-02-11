"""
Functions to create columns for analysis dataset.

All values are aggregated to user-freq frequency, where freq defaults do
'month'.

"""
import os

import numpy as np
import pandas as pd
from scipy.stats import entropy
import s3fs

from entropy import config
import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.helpers.helpers as hh


month = pd.Grouper(key="date", freq="m")
idx_cols = ["user_id", month]

aggregator_funcs = []


def aggregator(func):
    aggregator_funcs.append(func)
    return func


@aggregator
def user_id(df):
    return df.groupby(idx_cols).user_id.first()


@aggregator
def month_indicator(df):
    return df.groupby(idx_cols).date.first().dt.month.rename('month')


@hh.timer
@aggregator
def user_month_info(df):
    return df.groupby(idx_cols).agg(
        active_accounts=("account_id", "unique"),
        txns_count=("id", "nunique"),
        txns_value=("amount", lambda s: s.abs().sum()),
    )


@aggregator
@hh.timer
def txn_counts_by_account_type(df):
    group_cols = idx_cols + ["account_type"]
    return (
        df.groupby(group_cols, observed=True)
        .size()
        .unstack()
        .fillna(0)
        .loc[:, ["savings", "current"]]
        .rename(columns=lambda x: f"txn_count_{x[0]}a")
    )


@aggregator
@hh.timer
def month_spend(df):
    """Spend and log spend per user-month.

    We ignore log of zero cases since numpy can handle them by returning -inf
    and users with zero spend months will be dropped during sample selection.
    """
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)
    with np.errstate(divide="ignore"):
        return df.groupby(idx_cols).amount.agg(
            month_spend="sum", log_month_spend=lambda s: np.log(s.sum())
        )


@aggregator
@hh.timer
def tag_month_spend(df):
    """Spend per tag per user-month as proportion of total month spend."""
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)
    df["tag"] = df.tag.where(is_spend, np.nan)
    df["tag"] = df.tag.cat.rename_categories(lambda x: "prop_spend_" + x)
    group_cols = idx_cols + ["tag"]
    return (
        df.groupby(group_cols, observed=True)
        .amount.sum()
        .unstack()
        .fillna(0)
        .pipe(lambda df: df.div(df.sum(1), axis=0))
    )


@aggregator
@hh.timer
def income(df):
    """Annual and month income.

    Incomes are multiplied by -1 to get positive numbers (credits are negative
    in dataset). Annual incomes are scaled to 12-month incomes to account for
    user-years with incomplete data.
    """
    df = df.copy()
    is_income_pmt = df.tag_group.eq("income") & ~df.debit
    df["amount"] = df.amount.where(is_income_pmt, np.nan)
    user_year = lambda x: (x[0], x[1].year)
    scaled_income = lambda s: s.sum() / s.size * 12

    month_income = df.groupby(idx_cols).amount.sum().mul(-1).rename("month_income")
    annual_income = (
        month_income.groupby(user_year).transform(scaled_income).rename("annual_income")
    )

    return pd.concat([month_income, annual_income], axis=1)


@aggregator
@hh.timer
def entropy_spend_tag_counts(df):
    """Adds Shannon entropy scores based on tag counts of spend txns."""
    data = df.copy()
    is_spend = data.tag_group.eq("spend") & data.debit
    data["tag"] = data.tag.where(is_spend, np.nan)
    group_cols = idx_cols + ["tag"]
    g = data.groupby(group_cols, observed=True)

    tag_txns = g.size().unstack().fillna(0)
    total_txns = tag_txns.sum(1)
    num_unique_tags = len(tag_txns.columns)
    tag_probs = (tag_txns + 1).div(total_txns + num_unique_tags, axis=0)
    user_month_entropy = entropy(tag_probs, base=2, axis=1)
    return pd.Series(user_month_entropy, index=tag_probs.index).rename("entropy_sptac")


def _get_region():
    """Returns table with region names for each region code."""
    path = "s3://3di-data-ons/nspl/NSPL_AUG_2020_UK/raw/Documents"
    filename = "Region names and codes EN as at 12_10 (GOR).csv"
    fp = os.path.join(path, filename)
    df = ha.read_csv(fp, usecols=["GOR10CD", "GOR10NM"]).rename(
        columns={"GOR10CD": "region_code", "GOR10NM": "region"}
    )
    # remove pseudo region code indicators (e.g. '(pseudo) Wales' -> 'Wales')
    df["region"] = df.region.str.replace(r"\(pseudo\) ", "", regex=True)
    return df[["region_code", "region"]]


def _get_pcsector(**kwargs):
    """Returns table with region code for each postcode sector."""
    fp = "s3://3di-data-ons/nspl/NSPL_AUG_2020_UK/raw/Data/NSPL_AUG_2020_UK.csv"
    df = ha.read_csv(fp, usecols=["pcds", "rgn", "doterm"], **kwargs).rename(
        columns={"pcds": "postcode", "rgn": "region_code"}
    )
    # keep active postcodes only (those without a 'date of termination' date)
    df = df[df.doterm.isna()]
    # keep first occurring region code for each postcode sector
    df["pcsector"] = df.postcode.str.lower().str[:-2]
    df = df.drop_duplicates(subset=["pcsector"], keep="first")
    return df[["pcsector", "region_code"]]


def _make_region_lookup_table(**kwargs):
    """Returns table with region name for each postcode sector."""
    region = _get_region()
    pcsector = _get_pcsector(**kwargs)
    df = pcsector.merge(region, how="inner", on="region_code", validate="m:1")
    df["region_code"] = df.region_code.astype("category")
    df = df[["pcsector", "region"]]
    filename = "region_lookup_table.parquet"
    filepath = os.path.join(config.AWS_BUCKET, filename)
    ha.write_parquet(df, filepath)
    return df


def _get_regions_lookup_table():
    """Returns region lookup table."""
    fs = s3fs.S3FileSystem(profile=config.AWS_PROFILE)
    filename = "region_lookup_table.parquet"
    filepath = os.path.join(config.AWS_BUCKET, filename)
    if fs.exists(filepath):
        return ha.read_parquet(filepath)
    else:
        return _make_region_lookup_table()


@aggregator
@hh.timer
def region_name(df):
    df = df.copy()
    regions = _get_regions_lookup_table().rename(columns={"pcsector": "postcode"})
    df = df.merge(regions, how="left", on="postcode", validate="m:1")
    return df.groupby(idx_cols).region.first()


@aggregator
@hh.timer
def age(df):
    """Adds user age at time of transaction."""
    df = df.copy()
    df["age"] = df.date.dt.year - df.yob
    return df.groupby(idx_cols).age.first()


@aggregator
@hh.timer
def female(df):
    """Dummy for whether user is a women."""
    return df.groupby(idx_cols).female.first()


@aggregator
@hh.timer
def savings_accounts_flows(df):
    """Monthly savings account inflows."""
    df = df.copy()
    df["amount"] = df.amount.mul(-1)
    is_sa_inflow = (
        df.account_type.eq("savings")
        & df.amount.ge(5)
        & ~df.debit
        & ~df.tag_auto.str.contains("interest", na=False)
        & ~df.desc.str.contains(r"save\s?the\s?change", na=False)
    )
    df['amount'] = df.amount.where(is_sa_inflow, 0)
    return df.groupby(idx_cols).amount.agg(
        sa_inflows=("sum"),
        has_sa_inflows=(lambda x: (x.max() > 0).astype(int))
    )

