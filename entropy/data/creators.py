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
def calc_balances(df, window=3, aggfunc='mean'):
    """Calculate daily balances.

    Default calculates balance for each day as the mean of the balances of
    the current day and the two subsequent days.
    """
    def helper(g):
        mask = g.desc.eq('_balance')
        latest_balance = g[mask].amount.values[0]
        refresh_date = g[mask].date.dt.date.values[0]

        pre_refresh = g.date.dt.date < refresh_date
        # pre_refresh_balances = (
        #     g[pre_refresh]
        #     .set_index('date')
        #     .resample('D').amount.sum()
        #     .sort_index(ascending=False)
        #     .rolling(window=window, min_periods=1).agg(aggfunc)
        #     .cumsum()
        #     .add(latest_balance)
        # )
        # post_refresh_balances = (
        #     g[~pre_refresh]
        #     .set_index('date')
        #     .resample('D').amount.sum().mul(-1)
        #     .sort_index(ascending=True)
        #     .rolling(window=window, min_periods=1).agg(aggfunc)
        #     .cumsum()
        # )
        # return (
        #     pre_refresh_balances
        #     .append(post_refresh_balances)
        #     .sort_index()
        #     .rename('balance')
        # )
        return g

    data = _latest_balance_as_row(df)
    balances = data.groupby('account_id').apply(helper).reset_index()
    # return df.merge(balances, how='left', validate='m:1')
    return data


def _latest_balance_as_row(df, zero_replace_value=np.nan):
    """Add latest balance as a temporary row.

    MDB data dict notes that exact zero values result from unsuccessful
    account refreshes. So, to be conservative, they are treated as missing
    by default.
    """
    cols = ['account_id', 'account_last_refreshed', 'latest_balance']
    latest_balances = df[cols].drop_duplicates().copy()
    latest_balances['desc'] = '_balance'
    new_names = {'account_last_refreshed': 'date', 'latest_balance': 'amount'}
    latest_balances.rename(columns=new_names, inplace=True)
    latest_balances.amount.replace(0, zero_replace_value, inplace=True)
    return df.append(latest_balances).sort_values(['account_id', 'date'])



def calc_balances(df):

    def helper(g):
        last_balance = g.latest_balance.iloc[0]
        last_refresh_date = g.account_last_refreshed.iloc[0]

        cumsum = g.set_index('date').resample('D').amount.sum().cumsum()

        pre_refresh = cumsum.truncate(after=last_refresh_date)
        cumsum_total = pre_refresh[-1]
        starting_balance = last_balance - cumsum_total

        return cumsum.add(starting_balance)

    balances = (df.groupby('account_id').apply(helper)
                .rename('balances').reset_index())
    return df.merge(balances, how='left', validate='m:1')




def calculate_salaries(df):
    """
    Return monthly and yearly salary for each user.

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
