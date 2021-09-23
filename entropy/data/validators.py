"""
Functions to validate integrity of final dataset.

"""

validator_funcs = []


def validator(func):
    """Add func to list of validator functions."""
    validator_funcs.append(func)
    return func


def tag(df):
    # check that tag only missing if tag_auto is missing
    return df




