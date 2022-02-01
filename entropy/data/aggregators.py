"""
Functions to create columns for analysis dataset.

All values are aggregated to user-freq frequency, where freq defaults do
'month'.

"""
import collections

import numpy as np
import pandas as pd

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
def user_month_info(df):
    return df.groupby(idx_cols).agg(
        active_accounts = ('account_id', 'unique'),
        txns_count = ('id', 'nunique'),
        txns_value = ('amount', lambda s: s.abs().sum()),
    )


@aggregator
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


## dev

@aggregator
def income(df):
    """Yearly income.

    Calculated yearly incomes are scaled to 12-month incomes to account for
    user-years with incomplete data and multiplied by -1 to get positive
    numbers (credits are negative in dataset).
    """
    year = pd.Grouper(key='date', freq='year')
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


## dev end




@aggregator
def income(df):
    """Adds income variables."""
    df = df.copy()
    df["log_income"] = np.log(df.income)
    cols = ["income", "log_income"]
    return df.groupby(idx_cols)[cols].first()


@aggregator
def savings_accounts_flows(df):
    """Monthly inflows, outflows, and net-inflows into user's savings accounts.

    Also calculates scaled flows by dividing by users monthly income.
    """
    df = df.copy()
    is_not_interest_txn = ~df.tag_auto.str.contains("interest", na=False)
    is_savings_account = df.account_type.eq("savings")
    is_savings_flow = is_not_interest_txn & is_savings_account
    df["amount"] = df.amount.where(is_savings_flow, np.nan)
    df["debit"] = df.debit.map({True: "sa_outflows", False: "sa_inflows"})
    group_cols = idx_cols + ["income", "debit"]
    return (
        df.groupby(group_cols)
        .amount.sum()
        .abs()
        .unstack()
        .fillna(0)
        .reset_index("income")
        .assign(
            sa_net_inflows=lambda df: df.sa_inflows - df.sa_outflows,
            sa_scaled_inflows=lambda df: df.sa_inflows / (df.income / 12),
            sa_scaled_outflows=lambda df: df.sa_outflows / (df.income / 12),
            sa_scaled_net_inflows=lambda df: df.sa_net_inflows / (df.income / 12),
        )
        .drop(columns="income")
    )


@aggregator
def monthly_spend(df):
    """Spend and log spend per user-month."""
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)

    return df.groupby(idx_cols).amount.agg(
        monthly_spend="sum", log_monthly_spend=lambda s: np.log(s.sum())
    )


@aggregator
def tag_monthly_spend_prop(df):
    """Spend per tag per user-month as proportion of total monthly spend."""
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
def demographics(df):
    """Adds demographic variable."""
    df = df.copy()
    df["age"] = df.date.dt.year - df.yob
    cols = ["female", "age", "region"]
    return df.groupby(idx_cols)[cols].first()


# @aggregator
def entropy(df):
    """Adds all entropy variables."""
    cols = hd.colname_subset(df, "entropy")
    return df.groupby(idx_cols)[cols].first()
