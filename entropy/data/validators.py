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


@validator
def spend_tag(df):
    """All occurring spend tags are valid."""
    spend_txns = df[df.tag_group.eq('spend')]
    occurring = set(spend_txns.tag.unique())
    valid = set(tc.spend_subgroups.keys())
    assert occurring <= valid


@validator
def no_gaps_and_min_obs(df):
    """Checks that user has no missing months and at least 5 txns per month.

    Test for no missing months happens for free because resample fills in
    missing months.
    """
    g = df.set_index('date').groupby('user_id')
    user_month_obs = g.resample('m').id.count()
    assert user_month_obs.min() >= 5



