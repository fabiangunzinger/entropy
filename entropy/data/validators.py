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
    occurring = set(df.tag_group.cat.categories)
    valid = set(tc.tag_groups.keys())
    assert occurring <= valid
    return df


@validator
def spend_tag(df):
    """All occurring spend tags are valid."""
    spend_txns = df[df.tag_group.eq('spend')]
    occurring = set(spend_txns.tag.unique())
    valid = set(tc.spend_subgroups.keys())
    assert occurring <= valid
    return df



