import math
import os
import s3fs

import numpy as np
import pandas as pd
from scipy.stats import entropy

import entropy.helpers.aws as ha
import entropy.helpers.helpers as hh
from entropy import config


creator_funcs = []


def creator(func):
    """Adds func to list of creator functions."""
    creator_funcs.append(func)
    return func


@creator
@hh.timer
def income(df):
    """
    Adds yearly income for each user.

    Calculated yearly incomes are scaled to 12-month incomes to account for
    user-years with incomplete data and multiplied by -1 to get positive
    numbers (credits are negative in dataset).
    """
    year = df.date.dt.year.rename("year")
    mask = df.tag_group.eq("income") & ~df.debit
    yearly_incomes = (
        df.loc[mask]
        .groupby(["user_id", year])
        .agg(income=("amount", "sum"), observed_months=("ym", "nunique"))
        .assign(income=lambda df: df.income / df.observed_months * -12)
        .drop(columns="observed_months")
    )
    return df.merge(
        yearly_incomes,
        left_on=["user_id", year],
        right_on=["user_id", "year"],
        validate="m:1",
    ).drop(columns="year")



@creator
@hh.timer
def age(df):
    """Adds user age at time of transaction."""
    df["age"] = df.date.dt.year - df.yob
    return df.drop("yob", axis=1)


@creator
@hh.timer
def entropy_spend_tag_counts(df):
    """Adds Shannon entropy scores based on tag counts of spend txns."""
    data = df.copy()
    is_spend = data.tag_group.eq("spend") & data.debit
    data["tag"] = data.tag.where(is_spend, np.nan)
    g = data.groupby(["user_id", "ym", "tag"], observed=True)
    tag_txns = g.size().unstack().fillna(0)

    total_txns = tag_txns.sum(1)
    num_unique_tags = len(tag_txns.columns)
    tag_probs = (tag_txns + 1).div(total_txns + num_unique_tags, axis=0)
    user_month_entropy = entropy(tag_probs, base=2, axis=1)
    s = pd.Series(user_month_entropy, index=tag_probs.index).rename("entropy_sptac")
    return df.merge(s, how="left", on=["user_id", "ym"], validate="m:1")


def entropy_spend_tag_counts_partial(df):
    """Adds Shannon entropy scores based on tag counts of spend txns."""
    data = df.copy()
    is_spend = data.tag_group.eq("spend") & data.debit
    data["tag"] = data.tag.where(is_spend, np.nan)
    g = data.groupby(["user_id", "ym", "tag"], observed=True)
    tag_txns = g.size().unstack().fillna(0)
    total_txns = tag_txns.sum(1)
    num_unique_tags = len(tag_txns.columns)
    tag_probs = (tag_txns + 1).div(total_txns + num_unique_tags, axis=0)
    return tag_probs
     
    user_month_entropy = entropy(tag_probs, base=2, axis=1)
    s = pd.Series(user_month_entropy, index=tag_probs.index).rename("entropy_sptac")
    return df.merge(s, how="left", on=["user_id", "ym"], validate="m:1")



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


@creator
@hh.timer
def region_name(df):
    regions = _get_regions_lookup_table().rename(columns={"pcsector": "postcode"})
    return df.merge(regions, how="left", on="postcode", validate="m:1")
