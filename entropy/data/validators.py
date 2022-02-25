"""
Functions to validate integrity of analysis data.

"""

import numpy as np
import entropy.data.txn_classifications as tc

validator_funcs = []


def validator(func):
    """Add func to list of validator functions."""
    validator_funcs.append(func)
    return func


@validator
def no_missing_values(df):
    assert df.isna().sum().sum() == 0
    return df


@validator
def year_income(df, lower=10_000):
    assert df.year_income.min() >= lower
    return df


@validator
def savings_account(df):
    assert df.groupby('user_id').txn_count_sa.max().gt(0).all()
    return df


@validator
def min_number_of_months(df):
    assert df.groupby('user_id').size().ge(6).all()
    return df


@validator
def month_min_spend(df):
    assert df.month_spend.min() >= 200
    return df


@validator
def month_min_ca_txns(df):
    assert df.txn_count_ca.min() >= 5
    return df


@validator
def complete_demographic_info(df):
    assert df.filter(regex='female|age').isna().sum().sum() == 0
    return df


@validator
def uniform_month_distribution(df):
    stats = ["min", "25%", "50%", "75%", "max"]
    assert all(df.month.describe()[stats] == [1, 3, 6, 9, 12])
    return df

