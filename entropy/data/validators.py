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


@validator
def val_current_and_savings_account(df):
    min_accounts = df.groupby(["user_id"]).account_type.value_counts().unstack().min()
    assert min_accounts['current'] > 0
    assert min_accounts['savings'] > 0


@validator
def val_min_number_of_months(df, min_months):
    assert df.groupby('user_id').ym.nunique().min() >= min_months


@validator
def val_account_balances_available(df):
    g = df[df.account_type.isin(['current', 'savings'])].groupby(["user_id", "account_id"])
    assert g.latest_balance.min().groupby('user_id').min().notna().all()
    assert g.account_last_refreshed.min().groupby('user_id').min().gt('1-1-2012').all()



