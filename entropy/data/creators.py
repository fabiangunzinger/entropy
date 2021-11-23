"""
Functions that create additional variables.

"""

import numpy as np
from scipy.stats import entropy
from entropy.data import helpers


creator_funcs = []


def creator(func):
    """Adds func to list of creator functions."""
    creator_funcs.append(func)
    return func


@creator
def balances(df):
    """Calculates running account balances.

    Daily account balance is calculated as the sum of the cumulative
    balance and the starting balance, where the starting balance is
    the difference between the cumulative balance and the actually
    reported balance on the day of the last refresh or the nearest
    preceeding date.
    """

    def helper(g):
        last_refresh_balance = g.latest_balance.iloc[0]
        last_refresh_date = g.account_last_refreshed.iloc[0].normalize()

        daily_net_spend = g.resample("D").amount.sum().mul(-1)
        cum_balance = daily_net_spend.cumsum()

        # get cum_balance on last refreshed date or nearest preceeding date
        idx = cum_balance.index.get_loc(last_refresh_date, method="ffill")
        print(cum_balance)
        return idx
        last_refresh_cum_balance = cum_balance[idx]

        starting_balance = last_refresh_balance - last_refresh_cum_balance
        balance = cum_balance + starting_balance
        return balance.rename("balance")

    balance = df.set_index('date').groupby("account_id").apply(helper).reset_index()
    return balance
    return df.merge(balance, how="left", validate="m:1")


@creator
def income(df):
    """Returns yearly income for each user.

    To account for years where we don't observe users for the
    full 12 months, we scale yearly income to represent a full
    12 months.
    """
    mask = df.tag_group.str.match("income", na=False)
    yearly_income_payments = (
        df.loc[mask].set_index("date").groupby("user_id").resample("Y")
    )
    yearly_payments_total = yearly_income_payments.amount.sum().mul(-1)
    yearly_unique_months = yearly_income_payments.ym.nunique()
    yearly_income = yearly_payments_total / yearly_unique_months * 12

    yearly_income = (
        yearly_income.rename("income")
        .reset_index()
        .assign(y=lambda df: df.date.dt.year)
        .drop(columns="date")
    )
    df["y"] = df.date.dt.year
    keys = ["user_id", "y"]
    merged = df.merge(yearly_income, how="left", on=keys, validate="m:1")
    return merged.drop(columns="y")


@creator
def entrop_scores(df):
    """Adds Shannon Entropy scores based on selected columns.

    Calculated at user-month level, based on `tag` and optionally
    additional columns.
    """

    def calc_entropy(g, column, unique_vals):
        total_txns = len(g)
        txns_by_cat = g.groupby(column).size()
        prop_by_cat = (txns_by_cat + 1) / (total_txns + unique_vals)
        return entropy(prop_by_cat, base=2)

    columns = ["tag"]
    for column in columns:
        col_name = "_".join(["entropy", column])
        unique_vals = df[column].nunique()
        scores = (
            df[df.debit]
            .groupby(["user_id", "ym"])
            .apply(calc_entropy, column, unique_vals)
            .rename(col_name)
            .reset_index()
        )
        df = df.merge(scores, validate="m:1")

    return df
