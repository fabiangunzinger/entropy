"""
Functions that perform sample selection. First line of docstring is being used
for description of procedure in sample selection table.

"""


import collections
import functools
import re
import pandas as pd


selector_funcs = []
sample_counts = collections.Counter()
FuncWithKwargs = collections.namedtuple("FuncWithKwargs", ["func", "kwargs"])


def selector(func=None, **kwargs):
    """Add function to list of selector functions."""

    def wrapper(func):
        selector_funcs.append(FuncWithKwargs(func, kwargs))
        return func

    return wrapper(func) if func else wrapper


def counter(func):
    """Count sample after applying function.

    First line of func docstring is used for description in selection table.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        df = func(*args, **kwargs)
        description = func.__doc__.splitlines()[0]
        sample_counts.update(
            {
                description + "@users": df.user_id.nunique(),
                description + "@accounts": df.account_id.nunique(),
                description + "@txns": df.id.nunique(),
                description + "@value": df.amount.abs().sum() / 1e6,
            }
        )
        return df

    return wrapper


@selector
@counter
def add_raw_count(df):
    """Raw sample
    Add count of raw dataset to selection table."""
    return df


@selector
@counter
def min_number_of_months(df, min_months=6):
    """At least 6 months of data"""
    cond = df.groupby("user_id").ym.transform("nunique") >= min_months
    return df.loc[cond]


@selector
@counter
def no_missing_months(df):
    """No missing months

    Requires that there are no months between first and last observed month for
    which we observe no transactions.
    """

    def month_range(date):
        return (date.max().to_period("M") - date.min().to_period("m")).n + 1

    g = df.groupby("user_id")
    months_observed = g.ym.transform("nunique")
    months_range = g.date.transform(month_range)
    return df.loc[months_observed == months_range]


@selector
@counter
def min_spend(df, min_txns=10, min_spend=200):
    """At least 5 monthly debits totalling \pounds200

    Drops first and last months for calculations because users will often have
    incomplete data for these months.
    """
    data = df.loc[df.debit, ["user_id", "id", "ym", "amount"]]

    g = data.groupby("user_id")
    first_month = g.ym.transform(min)
    last_month = g.ym.transform(max)
    data = data[data.ym.between(first_month, last_month, inclusive="neither")]

    g = data.groupby(["user_id", "ym"])
    min_monthly_spend = g.amount.sum().groupby("user_id").min()
    min_monthly_txns = g.size().groupby("user_id").min()
    conds = min_monthly_spend.ge(min_spend) & min_monthly_txns.ge(min_txns)
    users = conds[conds].index
    return df.loc[df.user_id.isin(users)]


@selector
@counter
def current_account(df):
    """At least one current account"""

    def helper(s):
        return s.eq("current").max()

    has_current_account = df.groupby("user_id").account_type.transform(helper)
    return df.loc[has_current_account]


@selector
@counter
def current_and_savings_account_balances(df):
    """Current and savings account balances available

    Keep only users for whom `latest_balance` is available for all
    current and savings accounts so we can calculate the running
    balance for all these accounts.
    """
    mask = df.account_type.isin(["current", "savings"]) & df.latest_balance.isna()
    users_to_drop = df[mask].user_id.unique()
    return df[~df.user_id.isin(users_to_drop)]


@selector
@counter
def income_pmts(df, income_months_ratio=2 / 3):
    """Income payments in 2/3 of all observed months"""

    def helper(g):
        num_months_observed = g.ym.nunique()
        num_months_with_income = g[g.tag_group.eq("income")].ym.nunique()
        return (num_months_with_income / num_months_observed) >= income_months_ratio

    return df.groupby("user_id").filter(helper)


@selector
@counter
def income_amount(df, lower=5_000, upper=200_000):
    """Yearly income between 5k and 200k

    Yearly income calculated on rolling basis from
    first month of data.
    """
    g = df.groupby('user_id')
    min_income = g.income.transform('min')
    max_income = g.income.transform('max')
    return df.loc[min_income.gt(lower) & max_income.lt(upper)]


@selector
@counter
def max_accounts(df, max_accounts=10):
    """No more than 10 active accounts in any year"""
    year = pd.Grouper(freq="Y", key="date")
    usr_max = (
        df.groupby(["user_id", year]).account_id.nunique().groupby("user_id").max()
    )
    users = usr_max[usr_max <= max_accounts].index
    return df[df.user_id.isin(users)]


@selector
@counter
def max_debits(df, max_debits=100_000):
    """Debits of no more than 100k in any month"""
    month = pd.Grouper(freq="M", key="date")
    debits = df[df.debit]
    usr_max = debits.groupby(["user_id", month]).amount.sum().groupby("user_id").max()
    users = usr_max[usr_max <= max_debits].index
    return df[df.user_id.isin(users)]


@selector
@counter
def valid_account_last_refreshed_date(df):
    """Last account refresh within observed period

    There are cases where last account refresh date is before the first date
    for which we observe an account, usually because it is set to a dummy date
    like 1 Jan 1900 for some reason.
    """

    def helper(g):
        return g.account_last_refreshed.iloc[0] >= g.date.min()

    return df.groupby("account_id").filter(helper)


# @selector
# @counter
def working_age(df, lower=18, upper=64):
    """Working-age"""
    age = 2021 - df.user_yob
    return df[age.between(lower, upper)]


@selector
@counter
def add_final_count(df):
    """Final sample
    Add count of final dataset to selection table."""
    return df
