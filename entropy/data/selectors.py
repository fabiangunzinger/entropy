"""
Functions to select users for analysis data.

First line in docstring is used in selection table.
"""

import collections
import functools
import itertools


selector_funcs = []
sample_counts = collections.Counter()


def selector(func):
    selector_funcs.append(func)
    return func


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
                description + "@user_months": len(df),
                description
                + "@accounts": len(
                    set(itertools.chain.from_iterable(df.active_accounts))
                ),
                description + "@txns": df.txns_count.sum(),
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
def annual_income(df, min_income=10_000):
    """Annual income of at least \pounds10k"""
    cond = (
        df.groupby("user_id").annual_income.apply(lambda x: x.min(skipna=False))
        >= min_income
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def regular_income(df, income_months_ratio=2 / 3):
    """Income in 2/3 of all observed months"""
    g = (df.month_income > 0).groupby(df.user_id)
    cond = g.sum() / g.size() >= income_months_ratio
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def savings_account(df):
    """At least one savings account"""
    cond = df.groupby("user_id").txn_count_sa.max().gt(0)
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def min_number_of_months(df, min_months=6):
    """At least 6 months of data"""
    cond = df.groupby("user_id").size() >= min_months
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def month_min_spend(df, min_spend=200):
    """Monthly debits of at least \pounds200"""
    cond = (
        df.groupby("user_id").month_spend.apply(lambda x: x.min(skipna=False))
        >= min_spend
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def month_min_ca_txns(df, min_txns=5):
    """Five or more current account txns per month"""
    cond = (
        df.groupby("user_id").txn_count_ca.apply(lambda x: x.min(skipna=False))
        >= min_txns
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def complete_demographic_info(df):
    """Complete demographic information

    Retains only users for which we have full demographic information.
    """
    cols = ["age", "female"]
    cond = df[cols].isna().groupby(df.user_id).sum().sum(1).eq(0)
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def add_final_count(df):
    """Final sample
    Add count of final dataset to selection table."""
    return df
