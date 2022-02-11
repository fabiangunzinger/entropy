"""
Functions to create columns for analysis dataset.

All values are aggregated to user-freq frequency, where freq defaults do
'month'.

"""
import os

import numpy as np
import pandas as pd
from scipy import stats
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
def tag_month_spend(df):
    """Spend per tag and total spend per user-month."""
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)
    df["tag"] = df.tag.where(is_spend, np.nan)
    df["tag"] = df.tag.cat.rename_categories(lambda x: "spend_" + x)
    group_cols = idx_cols + ["tag"]
    return (
        df.groupby(group_cols, observed=True)
        .amount.sum()
        .unstack()
        .fillna(0)
        .assign(month_spend=lambda df: df.sum(1))
        .apply(hd.winsorise, pct=1, how="upper")
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
    df["amount"] = df.amount.where(is_income_pmt, 0)

    user_year = lambda x: (x[0], x[1].year)
    scaled_income = lambda s: s.sum() / s.size * 12

    month_income = df.groupby(idx_cols).amount.sum().mul(-1).rename("month_income")
    annual_income = (
        month_income.groupby(user_year).transform(scaled_income).rename("annual_income")
    )

    return pd.concat([month_income, annual_income], axis=1).apply(
        hd.winsorise, pct=1, how="upper"
    )


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
    user_month_entropy = stats.entropy(tag_probs, base=2, axis=1)

    return pd.DataFrame(
        {"entropy": user_month_entropy, "entropyz": stats.zscore(user_month_entropy)},
        index=tag_probs.index,
    )


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
    df["amount"] = df.amount.where(is_sa_inflow, 0)
    return df.groupby(idx_cols).amount.agg(
        sa_inflows=("sum"), has_sa_inflows=(lambda x: (x.max() > 0).astype(int))
    )
