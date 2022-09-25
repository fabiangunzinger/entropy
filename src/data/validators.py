"""
Functions to validate integrity of analysis data.

"""
import functools

import numpy as np
import numpy as pd

import src.config as cf


validators = []


def validator(func):
    """Add func to list of validator functions."""
    validators.append(func)
    return func


@validator
def no_missing_values(df):
    exceptions = "^(?!entropy|std|dspend|sp_|ct_)"
    assert df.filter(regex=exceptions).notna().all().all()
    return df


# @validator
def tag_spend_counts(df):
    equal_to_txns_count_spend = functools.partial(
        pd.testing.assert_series_equal,
        right=df.txns_count_spend,
        check_dtype=False,
        check_names=False,
    )
    equal_to_txns_count_spend(df.filter(regex="^ct_tag_spend", axis=1).sum(1))
    equal_to_txns_count_spend(df.filter(regex="^ct_tag_(?!spend)", axis=1).sum(1))
    return df


# @validator
def tag_spend_value(df):
    equal_to_month_spend = functools.partial(
        pd.testing.assert_series_equal,
        right=df.month_spend,
        check_dtype=False,
        check_names=False,
        rtol=1,
    )
    equal_to_month_spend(df.filter(regex="^sp_tag_(?!spend)", axis=1).sum(1))
    equal_to_month_spend(df.filter(regex="^sp_tag_spend", axis=1).sum(1))
    return df


# @validator
def min_year_income(df, min_year_income=cf.MIN_YEAR_INCOME):
    min_month_income = round(min_year_income / 12, 2)
    assert df.month_income_mean.min() >= (min_month_income)
    return df


# @validator
def min_month_spend(df, min_spend=cf.MIN_MONTH_SPEND):
    assert df.month_spend.min() >= min_spend
    return df


@validator
def min_month_spend_txns(df, min_txns=cf.MIN_MONTH_SPEND_TXNS):
    assert df.txns_count_spend.min() >= min_txns
    return df


@validator
def complete_demographic_info(df):
    assert df.filter(regex="is_female|age|region").isna().sum().sum() == 0
    return df


@validator
def working_age(df):
    assert df.age.between(18, 65, inclusive="both").all()
    return df
