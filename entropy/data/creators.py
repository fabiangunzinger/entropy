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
def income(df):
    """Returns yearly income for each user.

    To account for years where we don't observe users for the 
    full 12 months, we scale yearly income to represent a full
    12 months.
    """
    mask = df.tag_group.str.match('income', na=False)
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
def entropy(df):
    """Return Shannon Entropy for user and column name."""
    from scipy.stats import entropy

    def calc_entropy(user, num_cats):
        total_txns = len(user)
        txns_by_cat = user.groupby(column).size()
        prop_by_cat = (txns_by_cat + 1) / (total_txns + num_cats)
        return entropy(prop_by_cat, base=2)

    g = df[df.debit].groupby('user_id')
    for column in ['tag_auto', 'tag']:
        col_name = '_'.join(['entropy', column])
        num_cats = df[column].nunique()
        scores = (g.apply(calc_entropy, num_cats)
                  .rename(col_name)
                  .reset_index())
        df = df.merge(scores, validate='m:1') 

    return df





