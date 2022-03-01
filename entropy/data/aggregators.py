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
def category_counts(df):
    """Counts number of unique spend categories for entropy category variables."""
    df = df.copy()
    cat_vars = ["tag", "tag_auto", "merchant"]
    is_spend = df.tag_group.eq("spend") & df.debit
    for var in cat_vars:
        df[var] = df[var].where(is_spend, np.nan)
    g = df.groupby(idx_cols)
    return pd.concat(
        (g[var].nunique().rename(f"nunique_{var}") for var in cat_vars), axis=1
    )


@aggregator
@hh.timer
def prop_credit(df):
    """Proportion of month spend paid by credit card."""
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)
    df["credit"] = np.where(df.account_type.eq("credit card"), "cc", "other")
    group_cols = idx_cols + ["credit"]
    return (
        df.groupby(group_cols)
        .amount.sum()
        .unstack()
        .fillna(0)
        .assign(prop_credit=lambda df: df.cc / df.sum(1))
        .drop(columns=["cc", "other"])
    )


@aggregator
@hh.timer
def income(df):
    """Income variables.

    Incomes are multiplied by -1 to get positive numbers (credits are negative
    in dataset), and expressed in '000s to ease coefficient comparison.

    `month_income` is sum of income payment in a given month.

    `year_income` is sum of income payments in calendar year, scaled to
    12-month incomes to account for user-years with incomplete data.

    `has_regular_income` is dummy indicating whether user received income in at least
    10 our of last 12 months.

    `has_month_income` is a dummy indicating whether user received income in
    current calendar month.
    """
    df = df.copy()
    is_income_pmt = df.tag_group.eq("income") & ~df.debit
    df["amount"] = df.amount.where(is_income_pmt, 0).mul(-1)

    user_year = lambda x: (x[0], x[1].year)
    scaled_inc = lambda s: s.sum() / s.size * 12

    mt_inc = (
        df.groupby(idx_cols)
        .amount.sum()
        .rename("month_income")
        .div(1000)
        .pipe(hd.winsorise, pct=1, how="upper")
    )

    yr_inc = (
        mt_inc.groupby(user_year)
        .transform(scaled_inc)
        .rename("year_income")
        .pipe(hd.winsorise, pct=1, how="upper")
    )

    has_reg_inc = (
        mt_inc.gt(0)
        .groupby("user_id")
        .rolling(window=12, min_periods=1)
        .sum()
        .gt(10)
        .astype(int)
        .droplevel(0)
        .rename("has_regular_income")
    )

    has_mt_inc = mt_inc.gt(0).astype(int).rename("has_month_income")

    return pd.concat([mt_inc, yr_inc, has_reg_inc, has_mt_inc], axis=1)


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
    user_month_entropy = stats.entropy(tag_probs, base=2, axis=1) / np.log2(
        num_unique_tags
    )

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
    """Monthly savings account inflows and dummy for savings habit."""
    df = df.copy()
    df["amount"] = df.amount.mul(-1)
    is_sa_inflow = (
        df.account_type.eq("savings")
        & ~df.debit
        & df.amount.ge(5)
        & ~df.tag_auto.str.contains("interest", na=False)
        & ~df.desc.str.contains(r"save\s?the\s?change", na=False)
    )
    df["amount"] = df.amount.where(is_sa_inflow, 0)

    data = df.groupby(idx_cols).amount.agg(
        sa_inflows=("sum"), has_sa_inflows=(lambda x: (x.max() > 0).astype(int))
    )

    data["has_reg_sa_inflows"] = (
        data.groupby("user_id")
        .has_sa_inflows.rolling(window=12, min_periods=1)
        .sum()
        .ge(10)
        .astype(int)
        .droplevel(0)
    )
    return data


@aggregator
@hh.timer
def benefits(df):
    """Dummy indicating (non-family) benefit receipt."""
    df = df.copy()
    p = r"^(?!family).*benefits"
    is_benefit = df.tag_auto.str.match(p, na=False)
    df["amount"] = df.amount.where(is_benefit, 0)
    return df.groupby(idx_cols).amount.sum().lt(0).astype(int).rename("has_benefits")


@aggregator
@hh.timer
def pension(df):
    """Dummy for whether user receives pension in current month."""
    df = df.copy()
    age = df.date.dt.year - df.yob
    is_pension = df.tag.eq("pensions") & age.ge(60)
    df["amount"] = df.amount.where(is_pension, 0)
    return df.groupby(idx_cols).amount.sum().lt(0).astype(int).rename("has_pension")


@aggregator
@hh.timer
def housing_payments(df):
    """Dummies for mortgage or rent payments.

    Classifying "mortgage or rent" auto tags as mortgages since data inspectio
    suggests that this is accurate for majority of cases.

    Cases where user makes both rent and mortgage payment in same month account
    for less than 2.5% of test dataset, so ignoring this issue.
    """
    df = df.copy()
    df["housing"] = np.where(
        df.tag_auto.str.match(r"rent", na=False),
        "rent",
        np.where(
            df.tag_auto.str.match(r"^mortgage (or rent|payment)$", na=False),
            "mortgage",
            "other",
        ),
    )
    df["housing"] = df.housing.astype("category")
    group_cols = idx_cols + ["housing"]
    return (
        df.groupby(group_cols, observed=True)
        .size()
        .unstack()
        .fillna(0)
        .drop(columns="other")
        .rename(columns=lambda x: "has_" + x + "_pmt")
    )


@aggregator
@hh.timer
def loans(df):
    """Dummies for receiving and repaying unsecured or payday loans."""
    df = df.copy()
    is_personal_loan = df.tag_auto.str.match(r"^(personal|unsecured) loan")
    is_payday_loan = df.tag_auto.str.match(r"^payday loan")
    df["loan"] = "other"
    df["loan"] = np.where(is_personal_loan & df.debit, "loan_repmt", df.loan)
    df["loan"] = np.where(is_personal_loan & ~df.debit, "loan_funds", df.loan)
    df["loan"] = np.where(is_payday_loan & df.debit, "pdloan_repmt", df.loan)
    df["loan"] = np.where(is_payday_loan & ~df.debit, "pdloan_funds", df.loan)
    group_cols = idx_cols + ["loan"]
    return (
        df.groupby(group_cols, observed=True)
        .size()
        .unstack()
        .drop(columns="other")
        .fillna(0)
        .gt(0)
        .astype(int)
    )


@aggregator
@hh.timer
def region(df):
    """Region and urban dummy."""
    return df.groupby(idx_cols)[["region_name", "is_urban"]].first()


@aggregator
@hh.timer
def month_spend(df):
    """Spend per tag and total spend per user-month.

    Expressed in '000s to ease coefficient comparison.
    """
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
        .div(1000)
        .apply(hd.winsorise, pct=1, how="upper")
    )


def _counts(df, cat, wknd=False):
    """Spend txns count for each cat by user-month.

    Args:
      df: A txn-level daframe.
      cat: A column from df to be used for categorising spending transactions.
      wknd: A Boolean indicating whether spend txns should be categorised
        by (cat, wknd), if True, or by (cat), if False, where wknd is a dummy
        indicating whether a txn is dated as a Sa, So, or Mo.
    Returns:
      A DataFrame with user-month rows, category columns, and count values.
    """
    is_cat_observed_spend = df.tag_group.eq("spend") & df.debit & df[cat].notna()
    df = df.loc[is_cat_observed_spend].copy()
    if wknd:
        is_wknd = df.date.dt.dayofweek.isin([5, 6, 0]).astype(str)
        df[cat] = df[cat].astype(str) + is_wknd
    group_cols = idx_cols + [cat]
    return df.groupby(group_cols, observed=True).size().unstack().fillna(0)


def _entropy(df, normalised=True, smooth=False):
    """Returns row-wise entropy scores based on counts.

    Args:
      df: A DataFrame with entity rows, category columns, and count values.
      normalised: A Boolean value indicating whether to divide entorpy by
        max entropy.
      smoothed: A Boolean value indicating whether to apply additive smoothing
        to the counts in df before calculating probabilities.
    Returns:
      A series with entropy scores for each row.
    """
    row_totals = df.sum(1)
    num_unique = len(df.columns)
    if smooth:
        probs = (df + 1).div(row_totals + num_unique, axis=0)
    else:
        probs = (df).div(row_totals, axis=0)
    e = stats.entropy(probs, base=2, axis=1)
    if normalised:
        e = e / np.log2(num_unique)
    return pd.Series(e, index=df.index)


@aggregator
@hh.timer
def count_based_entropy_scores(df):
    """Add count-based entropy measures."""
    cats = ["tag", "tag_auto", "merchant"]
    scores = []
    for cat in cats:
        scores.extend(
            [
                _entropy(_counts(df, cat, wknd=False)).rename(f"entropy_{cat}"),
                _entropy(_counts(df, cat, wknd=True)).rename(f"entropy_{cat}_wknd"),
            ]
        )

    
    return pd.concat(scores, axis=1)
