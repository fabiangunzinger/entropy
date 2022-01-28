"""
Functions to select users for analysis data.

First line in docstring is used in selection table.
"""

import collections
import functools
import re

import numpy as np
import pandas as pd

import entropy.helpers.helpers as hh


selector_funcs = []
sample_counts = collections.Counter()
FuncWithKwargs = collections.namedtuple("FuncWithKwargs", ["func", "kwargs"])


def selector(func=None, **kwargs):
    """Add function to list of selector functions."""

    def wrapper(func):
        selector_funcs.append(FuncWithKwargs(func, kwargs))
        return func

    return wrapper(func) if func else wrapper


def counter(func):
    """Count sample after applying function.

    First line of func docstring is used for description in selection table.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        df = func(*args, **kwargs)
        description = func.__doc__.splitlines()[0]
        sample_counts.update(
            {
                description + "@users": df.user_id.nunique(),
                description + "@accounts": df.account_id.nunique(),
                description + "@txns": df.id.nunique(),
                description + "@value": df.amount.abs().sum() / 1e6,
            }
        )
        return df

    return wrapper


@selector
@counter
def add_raw_count(df):
    """Raw sample
    Add count of raw dataset to selection table."""
    return df


@selector
@counter
def current_and_savings_account(df):
    """At least one current and one savings account"""
    s = df.groupby(["user_id", "account_type"]).size().unstack()
    cond = s.savings.gt(0) & s.current.gt(0)
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def min_number_of_months(df, min_months=6):
    """At least 6 months of data"""
    cond = df.groupby("user_id").ym.transform("nunique") >= min_months
    return df.loc[cond]


@selector
@counter
def no_missing_months(df):
    """No missing months

    Requires that there are no months between first and last observed month for
    which we observe no transactions.
    """

    def month_range(date):
        return (date.max().to_period("M") - date.min().to_period("m")).n + 1

    g = df.groupby("user_id")
    months_observed = g.ym.transform("nunique")
    months_range = g.date.transform(month_range)
    return df.loc[months_observed == months_range]


@selector
@counter
def monthly_min_spend(df, min_spend=200):
    """Current account debits of at least £200 each month"""
    is_ca_spend = df.tag_group.eq("spend") & df.account_type('current') & df.debit
    spend = df.amount.where(is_ca_spend, np.nan)
    cond = (
        spend.groupby([df.user_id, df.ym]).sum().groupby("user_id").min().ge(min_spend)
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def monthly_income_pmts(df, income_months_ratio=2 / 3):
    """Income in 2/3 of all observed months"""

    def helper(g):
        num_months_observed = g.ym.nunique()
        num_months_with_income = g[g.tag_group.eq("income")].ym.nunique()
        return (num_months_with_income / num_months_observed) >= income_months_ratio

    return df.groupby("user_id").filter(helper)


@selector
@counter
def annual_income(df, min_income=10_000):
    """Yearly income of at least \pounds10k"""
    cond = df.groupby("user_id").income.min() >= min_income
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def demographic_info(df):
    """Demographic information available

    Retains only users for which we have full demographic information.
    """
    cols = ["yob", "female", "region"]
    missings = df[cols].isna()
    cond = missings.groupby(df.user_id).sum().sum(1).eq(0)
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def add_final_count(df):
    """Final sample
    Add count of final dataset to selection table."""
    return df
