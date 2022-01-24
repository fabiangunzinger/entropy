"""
Functions to validate integrity of transactions dataset.

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
    spend_txns = df[df.tag_group.eq("spend")]
    occurring = set(spend_txns.tag.unique())
    valid = set(tc.spend_subgroups.keys())
    assert occurring <= valid


@validator
def val_current_and_savings_account(df):
    min_accounts = df.groupby(["user_id"]).account_type.value_counts().unstack().min()
    assert min_accounts["current"] > 0
    assert min_accounts["savings"] > 0


@validator
def val_account_balances_available(df):
    mask = df.account_type.isin(["current", "savings"])
    g = df[mask].groupby(["user_id", "account_id"])
    assert g.latest_balance.min().groupby("user_id").min().notna().all()
    assert g.account_last_refreshed.min().groupby("user_id").min().gt("1-1-2012").all()


@validator
def val_min_number_of_months(df, min_months=6):
    assert df.groupby("user_id").ym.nunique().min() >= min_months


@validator
def val_no_missing_months(df):
    def month_range(date):
        return (date.max().to_period("M") - date.min().to_period("m")).n + 1

    g = df.groupby("user_id")
    months_observed = g.ym.transform("nunique")
    months_range = g.date.transform(month_range)
    assert all(months_observed == months_range)


@validator
def val_min_monthly_grocery_txns(df, min_txns=4):
    s = df.tag_auto.eq("food, groceries, household") & df.debit
    assert all(
        s.groupby([df.user_id, df.ym]).sum().groupby("user_id").min() >= min_txns
    )


@validator
def val_monthly_income_pmts(df, income_months_ratio=2 / 3):
    months_with_income = (
        df.tag_group.eq("income")
        .groupby([df.user_id, df.ym])
        .sum()
        .gt(0)
        .groupby(["user_id"])
        .sum()
    )
    all_months = df.groupby("user_id").ym.nunique()

    return all(months_with_income / all_months > income_months_ratio)


@validator
def val_annual_income(df, lower=10_000, upper=500_000):
    assert (df.income.min() >= lower) and (df.income.max() <= upper)


@validator
def val_demographic_info(df):
    cols = ["yob", "female", "postcode"]
    assert df[cols].isna().sum().sum() == 0


