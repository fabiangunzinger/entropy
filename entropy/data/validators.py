"""
Functions to validate integrity of final dataset.

"""

import entropy.data.helpers as hr

validator_funcs = []


def validator(func):
    """Add func to list of validator functions."""
    validator_funcs.append(func)
    return func


@validator
def tag(df):
    # each txn is either one of defined tag groups or None
    expected = set(hr.tag_groups.keys())
    expected = expected.add(None)
    df.tag_group.unique == expected

    return df







