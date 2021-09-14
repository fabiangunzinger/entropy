"""
Functions that create additional variables.

"""

import numpy as np


creator_funcs = []


def creator(func):
    """Add func to list of creator functions."""
    creator_funcs.append(func)
    return func


@creator
def calc_balance(df):
    """Calculate running account balance.

    Daily account balance is calculated as the sum of the cumulative
    balance and the starting balance, which is the difference between
    the cumulative balance and the actually reported balance on the
    day of the last refresh.
    """
    def helper(g):
        last_refresh_balance = g.latest_balance.iloc[0]
        last_refresh_date = g.account_last_refreshed.iloc[0]
        
        daily_net_spend = g.set_index('date').resample('D').amount.sum()
        cum_balance = daily_net_spend.cumsum()

        # get cum_balance on last refreshed date or nearest preceeding date 
        idx = cum_balance.index.get_loc(last_refresh_date, method='ffill')
        last_refresh_cum_balance = cum_balance[idx]

        starting_balance = last_refresh_balance - last_refresh_cum_balance
        balance = cum_balance.add(starting_balance).rename('balance')
        return balance

    balance = df.groupby('account_id').apply(helper).reset_index()
    return df.merge(balance, how='left', validate='m:1')


@creator
def calc_income(df):
    """Return yearly income for each user.

    Data inspection suggests that most users get income payments
    every month of the year except in the first and last year we 
    observe them. We thus scale income to represent a full 
    12 months.
    """
    mask = df.tag.str.endswith('_income')
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


def calculate_salaries(df):
    """Return monthly and yearly salary for each user.

    Salaries are monthly/yearly aggregated sums of
    all transactions tagged as salaries by MDB.
    """
    def make_groupers(df):
        """Create user-year-month/user-year strings for merge."""
        y = df.date.dt.to_period('Y').astype('str')
        ym = df.date.dt.to_period('M').astype('str')
        str_id = df.user_id.astype('str')
        df['month_grouper'] = str_id + ' - ' + ym
        df['year_grouper'] = str_id + ' - ' + y
        return df

    def calc_monthly_salary(df):
        """Return monthly salary for each user."""
        tagsum = df[['auto_tag', 'manual_tag', 'tag']].sum(1)
        mask = tagsum.str.contains('salary')
        monthly_salary = (
            df[mask]
            .set_index(['user_id', 'date'])
            .groupby(level='user_id')
            .resample('M', level='date')
            .amount.sum().abs()
            .reset_index()
            .pipe(make_groupers)
            .drop(['date', 'user_id', 'year_grouper'], axis=1)
            .rename(columns={'amount': 'monthly_salary'})
        )
        return df.merge(monthly_salary, how='left', validate='m:1')

    def calc_yearly_salary(df):
        """Return yearly salary for each user."""
        tagsum = df[['auto_tag', 'manual_tag', 'tag']].sum(1)
        mask = tagsum.str.contains('salary')
        yearly_salary = (
            df[mask]
            .set_index(['user_id', 'date'])
            .groupby(level='user_id')
            .resample('Y', level='date')
            .amount.sum().abs()
            .reset_index()
            .pipe(make_groupers)
            .drop(['date', 'user_id', 'month_grouper'], axis=1)
            .rename(columns={'amount': 'yearly_salary'})
        )
        return df.merge(yearly_salary, how='left', validate='m:1')

    def drop_groupers(df):
        return df.drop(['month_grouper', 'year_grouper'], axis=1)

    def replace_nans(df):
        df['monthly_salary'] = df.monthly_salary.fillna(0)
        df['yearly_salary'] = df.yearly_salary.fillna(0)
        return df

    return (
        df
        .pipe(make_groupers)
        .pipe(calc_monthly_salary)
        .pipe(calc_yearly_salary)
        .pipe(drop_groupers)
        .pipe(replace_nans)
    )
