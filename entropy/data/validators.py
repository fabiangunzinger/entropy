"""
Functions to validate integrity of final dataset.

"""

validator_funcs = []


def validator(func):
    """Add func to list of validator functions."""
    validator_funcs.append(func)
    return func


