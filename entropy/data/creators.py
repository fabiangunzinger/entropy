import numpy as np
import pandas as pd
from scipy.stats import entropy


creator_funcs = []


def creator(func):
    """Adds func to list of creator functions."""
    creator_funcs.append(func)
    return func


@creator
def balances(df):
    """Adds running account balances.

    Daily account balance is calculated as the sum of the cumulative
    balance and the offset, where the offset is the difference between
    the cumulative balance and the actually reported balance on the day
    of the last refresh or the nearest preceeding date.
    """

    def helper(g):
        last_refresh_balance = g.latest_balance.iloc[0]
        last_refresh_date = g.account_last_refreshed.iloc[0].normalize()

        daily_net_spend = g.resample("D").amount.sum().mul(-1)
        cum_balance = daily_net_spend.cumsum()
        try:
            # get cum_balance on last refreshed date or nearest preceeding date
            # fails if last refresh date is dummy date outside the period we
            # observe a user.
            idx = cum_balance.index.get_loc(last_refresh_date, method="ffill")
        except KeyError:
            last_refresh_cum_balance = np.nan
        else:
            last_refresh_cum_balance = cum_balance[idx]

        offset = last_refresh_balance - last_refresh_cum_balance
        balance = cum_balance + offset
        return balance.rename("balance")

    balance = df.set_index("date").groupby("account_id").apply(helper).reset_index()
    return df.merge(balance, how="left", validate="m:1")


@creator
def income(df):
    """
    Adds yearly income for each user.

    Calculated yearly incomes are scaled to 12-month incomes to account for
    user-years with incomplete data and multiplied by -1 to get positive
    numbers (credits are negative in dataset).
    """
    year = df.date.dt.year.rename("year")
    yearly_incomes = (
        df.loc[df.tag_group.eq("income")]
        .groupby(["user_id", year])
        .agg({"amount": "sum", "ym": "nunique"})
        .rename(columns={"amount": "income", "ym": "observed_months"})
        .assign(income=lambda df: df.income / df.observed_months * -12)
        .drop(columns="observed_months")
    )
    return df.merge(
        yearly_incomes,
        left_on=["user_id", year],
        right_on=["user_id", "year"],
        validate="m:1",
    ).drop(columns="year")


@creator
def age(df):
    """Adds age for each user."""
    df['user_age'] = 2021 - df.user_yob
    df.drop('user_yob', axis=1)
    return df


@creator
def entropy_spend_tag_counts(df):
    """Adds Shannon Entropy scores based on tag counts of spend txns."""

    def calc_entropy(g, num_unique_tags):
        num_total_txns = len(g)
        num_txns_by_cat = g.groupby("tag").size()
        prop_by_cat = (num_txns_by_cat + 1) / (num_total_txns + num_unique_tags)
        return entropy(prop_by_cat, base=2)

    spend = df[df.tag_group.eq("spend")].copy()
    spend["tag"] = spend.tag.cat.remove_unused_categories()
    num_unique_tags = spend.tag.nunique()
    entropy_scores = (
        spend.groupby(["user_id", "ym"])
        .apply(calc_entropy, num_unique_tags)
        .rename("entropy_sptac")
        .reset_index()
    )
    return df.merge(entropy_scores, on=["user_id", "ym"], validate="m:1")
