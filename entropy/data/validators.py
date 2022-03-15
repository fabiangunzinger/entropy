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
def year_income(df, min_income=10_000):
    assert df.year_income.min() >= (min_income / 1000)
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
def month_min_spend(df, min_spend=200):
    assert df.month_spend.min() >= (min_spend / 1000)
    return df


@validator
def month_min_ca_txns(df):
    assert df.txn_count_ca.min() >= 5
    return df


@validator
def complete_demographic_info(df):
    assert df.filter(regex='is_female|age|region').isna().sum().sum() == 0
    return df


