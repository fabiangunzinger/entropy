"""
Functions to validate integrity of final dataset.

"""

import entropy.data.txn_classifications as tc

validator_funcs = []


def validator(func):
    """Add func to list of validator functions."""
    validator_funcs.append(func)
    return func


@validator
def tag_groups(df):
    """All occurring tag groups are valid."""
    actual = set(df.tag_group.unique())
    expected = set(tc.tag_groups.keys())
    assert actual <= expected
    return df


@validator
def spend_tag(df):
    """All occurring spend tags are valid."""
    actual = set(df[df.tag_group.eq('spend')].tag.unique())
    expected = set(tc.spend_subgroups.keys())
    assert actual <= expected
    return df



