"""
Functions to validate integrity of analysis data.

"""

import numpy as np

import src.config as cf


validators = []


def validator(func):
    """Add func to list of validator functions."""
    validators.append(func)
    return func


@validator
def no_missing_values(df):
    exceptions = "^(?!entropy|std|dspend)"
    assert df.filter(regex=exceptions).notna().all().all()
    return df


@validator
def at_least_min_year_income(df, min_year_income=cf.MIN_YEAR_INCOME):
    min_month_income = round(min_year_income / 12, 2)
    assert df.month_income_mean.min() >= (min_month_income)
    return df


@validator
def min_month_spend(df, min_spend=cf.MIN_MONTH_SPEND):
    assert df.month_spend.min() >= min_spend
    return df


@validator
def min_month_txns(df, min_txns=cf.MIN_MONTH_TXNS):
    assert df.txns_count.min() >= min_txns
    return df


@validator
def complete_demographic_info(df):
    assert df.filter(regex="is_female|age|region").isna().sum().sum() == 0
    return df


@validator
def working_age(df):
    assert df.age.between(18, 65, inclusive="both").all()
    return df
