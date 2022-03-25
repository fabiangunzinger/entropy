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
                description + "@txns": df.txns_count.sum(),
                description + "@txns_volume": df.txns_volume.sum() / 1e6,
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
def year_income(df, min_income=10_000):
    """Annual income of at least \pounds10k

    min_income divided by 1000 because income expressed in '000s.
    """
    cond = df.groupby("user_id").year_income.apply(lambda x: x.min(skipna=False)) >= (
        min_income / 1000
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
    """Monthly debits of at least \pounds200

    min_spend divided by 1000 as spend is expressed in '000s.
    """
    cond = df.groupby("user_id").month_spend.apply(lambda x: x.min(skipna=False)) >= (
        min_spend / 1000
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def month_min_ca_txns(df, min_txns=5):
    """Five or more monthly current account txns"""
    cond = (
        df.groupby("user_id").txn_count_ca.apply(lambda x: x.min(skipna=False))
        >= min_txns
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


# @selector
# @counter
# def min_num_unique_categories(df, min_nunique=2):
#     """Spends in two distinct categories each month

#     Requires that user makes spend in at least two distinct categories in each
#     month for each category variable we use to calculate entorpy.

#     Ensures that we can calculate entropy scores (which requires spend in at
#     least one category) and avoids zero entropy scores (resulting from all
#     spends in one category) that are likely due to missing tags.
#     """
#     cond = df.filter(regex="^nunique_").min(1).groupby(df.user_id).min().ge(min_nunique)
#     users = cond[cond].index
#     return df[df.user_id.isin(users)]


@selector
@counter
def min_spend_diversity(df):
    """Minimum level of spend diversity

    Requiring that entropy is larger than 0 ensures that there are at txns in
    at least two categories per user-month. For all but grocery entropy, fewer
    than that likely indicates incomplete tagging rather than genuine counts.

    For groceries, it's possible that all txns are with the same grocer in a
    user-month, so we require that grocery entropy is not missing, which
    ensures that there is at least a single tagged txn.
    """
    raw_non_groc_entropies = df.filter(regex="entropy(?!.*_([sz]|groc))")
    cond = (raw_non_groc_entropies.min(1).groupby(df.user_id).min() > 0) & (
        df.entropy_groc.notna().groupby(df.user_id).min() == 1
    )
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def complete_demographic_info(df):
    """Complete demographic information

    Retains only users for which we have full demographic information.
    """
    cols = ["age", "is_female", "is_urban"]
    cond = df[cols].isna().groupby(df.user_id).sum().sum(1).eq(0)
    users = cond[cond].index
    return df[df.user_id.isin(users)]


@selector
@counter
def add_final_count(df):
    """Final sample
    Add count of final dataset to selection table."""
    return df
