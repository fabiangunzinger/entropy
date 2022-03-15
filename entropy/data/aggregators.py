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
    is_spend = df.tag_group.eq("spend") & df.is_debit
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
    is_spend = df.tag_group.eq("spend") & df.is_debit
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
    is_income_pmt = df.tag_group.eq("income") & ~df.is_debit
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
def age(df):
    """Adds user age at time of transaction."""
    df = df.copy()
    df["age"] = df.date.dt.year - df.birth_year
    return df.groupby(idx_cols).age.first()


@aggregator
@hh.timer
def female(df):
    """Dummy for whether user is a women."""
    return df.groupby(idx_cols).is_female.first()


@aggregator
@hh.timer
def savings_accounts_flows(df):
    """Saving accounts flows variables.

    Calculates in, out, and netflows, and dummies for whether there were
    any inflows and whether there are regular inflows (defined as inflows in 10 out of last 12 months).

    Args:
    df: Txn DataFrame.

    Returns:
    Series with user-month index and calculated variables.
    """
    sa_flows = df.amount.where(df.is_sa_flow == 1, 0)
    in_out = df.is_debit.map({True: "sa_inflows", False: "sa_outflows"})
    group_vars = [df.user_id, df.ym, in_out]

    return (
        sa_flows.groupby(group_vars)
        .sum()
        .abs()
        .unstack()
        .assign(
            sa_netflows=lambda df: df.sa_inflows - df.sa_outflows,
            has_sa_inflows=lambda df: (df.sa_inflows > 0).astype(int),
            has_reg_sa_inflows=lambda df: (
                df.groupby("user_id")
                .has_sa_inflows.rolling(window=12, min_periods=1)
                .sum()
                .ge(10)
                .astype(int)
                .droplevel(0)
            ),
        )
    )


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
    age = df.date.dt.year - df.birth_year
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
def loan_funds_and_repayments(df):
    """Dummies for receiving and repaying loans."""
    df = df.copy()
    is_loan = df.tag_auto.str.match(r"(personal|unsecured|payday) loan")
    df["loan"] = "other"
    df["loan"] = np.where(is_loan & df.is_debit, "loan_repmt", df.loan)
    df["loan"] = np.where(is_loan & ~df.is_debit, "loan_funds", df.loan)
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
    is_spend = df.tag_group.eq("spend") & df.is_debit
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


@aggregator
@hh.timer
def overdraft_fees(df):
    """Dummy for whether overdraft fees were paid."""
    df = df.copy()
    pattern = r"(?:od|o/d|overdraft).*(?:fee|interest)"
    is_charge = df.desc.str.contains(pattern) & df.is_debit
    df["id"] = df.id.where(is_charge, np.nan)
    return df.groupby(idx_cols).id.count().gt(0).astype(int).rename("has_od_fees")


def _entropy_counts(df, cat, wknd=False):
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
    is_cat_observed_spend = df.tag_group.eq("spend") & df.is_debit & df[cat].notna()
    df = df.loc[is_cat_observed_spend].copy()
    if wknd:
        is_wknd = df.date.dt.dayofweek.isin([5, 6, 0]).astype(str)
        df[cat] = df[cat].astype(str) + is_wknd
    group_cols = idx_cols + [cat]
    return df.groupby(group_cols, observed=True).size().unstack().fillna(0)


def _entropy_scores(df, normalise=False, standardise=False, smooth=False):
    """Returns row-wise Shannon entropy scores based on counts.

    Args:
    df: A DataFrame with entity rows, category columns, and count values.
    normalise: A Boolean value indicating whether to divide entorpy by
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
    if normalise:
        e = e / np.log2(num_unique)
    if standardise:
        e = (e - e.mean()) / e.std()
    return pd.Series(e, index=df.index)


def _entropy_name(cat, wknd, smooth, standardise):
    name = f"entropy_{cat}"
    if wknd or smooth or standardise:
        name += "_"
    if wknd:
        name += "w"
    if smooth:
        name += "s"
    if standardise:
        name += "z"
    return name


@aggregator
@hh.timer
def count_based_entropy_scores(df):
    """Add count-based entropy measures."""
    cats = ["tag", "tag_auto", "merchant"]
    scores = []
    for cat in cats:
        for wknd in [True, False]:
            for smooth in [True, False]:
                for standardise in [True, False]:
                    name = _entropy_name(cat, wknd, smooth, standardise)
                    counts = _entropy_counts(df, cat, wknd=wknd)
                    score = _entropy_scores(
                        counts, standardise=standardise, smooth=smooth
                    ).rename(name)
                    scores.append(score)
    return pd.concat(scores, axis=1)
