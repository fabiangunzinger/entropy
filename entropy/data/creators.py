"""
Functions that create additional variables.

"""

import numpy as np
from entropy.data import helpers


creator_funcs = []


def creator(func):
    """Adds func to list of creator functions."""
    creator_funcs.append(func)
    return func


@creator
def calc_balance(df):
    """Calculates running account balance.

    Daily account balance is calculated as the sum of the cumulative
    balance and the starting balance, where the starting balance is
    the difference between the cumulative balance and the actually
    reported balance on the day of the last refresh or the nearest
    preceeding date.
    """
    def helper(g):
        last_refresh_balance = g.latest_balance.iloc[0]
        last_refresh_date = g.account_last_refreshed.iloc[0]
        
        daily_net_spend = g.set_index('date').resample('D').amount.sum()
        cum_balance = daily_net_spend.cumsum().mul(-1)

        # get cum_balance on last refreshed date or nearest preceeding date 
        idx = cum_balance.index.get_loc(last_refresh_date, method='ffill')
        last_refresh_cum_balance = cum_balance[idx]

        starting_balance = last_refresh_balance - last_refresh_cum_balance
        balance = cum_balance + starting_balance
        return balance.rename('balance')

    balance = df.groupby('account_id').apply(helper).reset_index()
    return df.merge(balance, how='left', validate='m:1')


@creator
def calc_income(df):
    """Returns yearly income for each user.

    To account for years where we don't observe users for the 
    full 12 months, we scale yearly income to represent a full
    12 months.
    """
    mask = df.tag.str.endswith('_income', na=False)
    yearly_income_payments = (df.loc[mask]
                              .set_index('date')
                              .groupby('user_id')
                              .resample('Y'))
    yearly_payments_total = yearly_income_payments.amount.sum().mul(-1)
    yearly_unique_months = yearly_income_payments.ym.nunique()
    yearly_income = yearly_payments_total / yearly_unique_months * 12
    
    yearly_income = (yearly_income
                     .rename('income')
                     .reset_index()
                     .assign(y=lambda df: df.date.dt.year)
                     .drop(columns='date'))
    df['y'] = df.date.dt.year
    keys = ['user_id', 'y']
    merged = df.merge(yearly_income, how='left', on=keys, validate='m:1')
    return merged.drop(columns='y')


@creator
def tag_savings(df):
    """Tags all txns with auto tag indicating savings."""
    df['savings'] = df.tag_auto.isin(helpers.savings)
    return df


