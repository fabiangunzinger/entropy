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

    Retains only users form whom we can calculate running balances.
    This requires a non-missing `latest_balance` and a valid
    `account_last_refreshed` date. The latter is invalid if its before the
    period during which we observe the user, which happens in a few cases
    where the date is set to a dummy date like 1 Jan 1990.
    """
    current_or_savings_account = df.account_type.isin(["current", "savings"])
    latest_balance_available = df.latest_balance.notna()
    user_first_observed = df.groupby('user_id').date.transform('min')
    valid_refresh_date = df.account_last_refreshed >= user_first_observed
    return df.loc[
        current_or_savings_account & latest_balance_available & valid_refresh_date
    ]


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
    """Yearly income between 5k and 200k"""
    g = df.groupby("user_id")
    min_income = g.income.transform("min")
    max_income = g.income.transform("max")
    return df.loc[min_income.gt(lower) & max_income.lt(upper)]


@selector
@counter
def max_accounts(df, max_accounts=10):
    """No more than 10 active accounts in any year"""
    year = pd.Grouper(freq="Y", key="date")
    max_num_accounts_in_year = (
        df.groupby(["user_id", year])
        .account_id.transform("nunique")
        .groupby(df.user_id)
        .transform(max)
    )
    return df.loc[max_num_accounts_in_year <= max_accounts]


@selector
@counter
def max_debits(df, max_debits=100_000):
    """Debits of no more than 100k in any month"""
    user_monthly_spend_max = (
        df[df.debit].groupby(["user_id", "ym"]).amount.sum().groupby("user_id").max()
    )
    users = user_monthly_spend_max[user_monthly_spend_max <= max_debits].index
    return df[df.user_id.isin(users)]


@selector
@counter
def add_final_count(df):
    """Final sample
    Add count of final dataset to selection table."""
    return df
