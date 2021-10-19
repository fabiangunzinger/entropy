"""
Create all figures.

Approach:
1. Load main dataset
2. One function per figure, which produces data used in figure and figure
itself.
3. Use styling helpers across functions whenever possible.

"""

import functools
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from entropy import config


def _set_style():
    plt.style.use(['seaborn-colorblind', 'seaborn-whitegrid'])


def _set_size(fig):
    fig.set_size_inches(8, 5)
    fig.tight_layout()


def _save_fig(fig, name):
    DPI = 1200
    fp = os.path.join(config.FIGDIR, name)
    fig.savefig(fp, dpi=DPI)
    print(f'{name} written.')

    
def income_distr(df):
    """Plots histogram of annual incomes."""
    incomes = df.groupby(['user_id', df.date.dt.year]).income.first()
    fig = sns.displot(incomes, aspect=2)
    _save_fig(fig, 'income_distr.png')



def balances_by_account_type(df, write=True):

    def make_data(
        df,
        account_type='current',
        freq='w',
        agg='median',
        start=None,
        end=None
    ):
        """Returns user balances at specified freq by account type."""
        return (df.loc[df.account_type.isin(account_type)]
                # single daily balance for each account
                .set_index('date')
                .groupby(['account_type', 'account_id'])
                .resample('d').balance.first()
                # median daily balance per account type
                .groupby(['date', 'account_type']).median()
                # one column per account type with legend labels
                .unstack()
                .rename(columns=lambda x: ' '.join([x.title(), 'accounts']))
                .rename_axis(columns=lambda x: x.replace('_', ' ').title())
                .resample(freq).agg(agg)
                .loc[start:end])

    def draw_plot(df):
        linestyles = [k for k, v in mpl.lines.lineStyles.items()]
        markers = [k for k, v in mpl.markers.MarkerStyle.markers.items()]
        fig, ax = plt.subplots()
        for i, col in enumerate(df):
            ax.plot(df[col], label=col, linestyle=linestyles[i])
        ax.legend(title=df.columns.name)
        return fig, ax

    def set_labels(ax):
        ax.set_xlabel('Year')
        ax.set_ylabel('Median account balance (£)')

    data = make_data(df, account_type=['current', 'savings'], start='2015')    
    fig, ax = draw_plot(data)
    set_labels(ax)
    _set_size(fig)
    if write: 
        _save_fig(fig, 'balances_by_account_type.png')


def monthly_txns_by_account_type(df, write=True):

    def make_data(df):
        return (df.loc[df.account_type.ne('other')]
                .set_index('date')
                .groupby(['account_type', 'account_id'], observed=True)
                .resample('M').id.count()
                .rename('num_txns')
                .reset_index())

    def make_plot(df):
        fig, ax = plt.subplots()
        ax = sns.boxenplot(data=df, x='num_txns', y='account_type')
        return fig, ax

    def set_labels(ax):
        # capitalise first letter of and add 'account' suffix to ytick labels
        to_label = lambda x: ' '.join([x[0].upper() + x[1:], 'accounts'])
        ytick_labels = [to_label(i.get_text()) for i in ax.get_yticklabels()]
        ax.set_yticklabels(ytick_labels)

        ax.set_xlabel('Number of transactions per month')
        ax.set_ylabel('')
    
    fig, ax = make_plot(make_data(df))
    set_labels(ax)
    _set_size(fig)
    if write:
        _save_fig(fig, 'monthly_txns_by_account_type.png')



def txns_distrs(df, write=True):
    """Plots distibutions of txns, spending categories, and entropy."""
    def make_txns_hist(g):
        data = g.id.count()
        histplot(data=data, bins=20, ax=ax[0])
        ax[0].set(xlabel='Transactions', ylabel=ylabel)    

    def make_spend_cat_hist(g):
        data = g.tag.nunique()
        bins = np.arange(df.tag.nunique() + 1) - 0.5
        histplot(data=data, bins=bins, ax=ax[1])
        ax[1].set(xlabel='Spending categories', ylabel=ylabel)

    def make_entropy_hist(g):
        data = g.entropy_tag.first()
        histplot(data=data, bins=20, ax=ax[2])
        ax[2].set(xlabel='Entropy', ylabel=ylabel)

    def set_size(fig):
        fig.set_size_inches(8, 2.5)
        fig.tight_layout()

    g = df.set_index('date').groupby('user_id').resample('M')
    histplot = functools.partial(sns.histplot, stat='percent')
    ylabel = 'User-months (%)'

    fig, ax = plt.subplots(1, 3)
    make_txns_hist(g)
    make_spend_cat_hist(g)
    make_entropy_hist(g)
    set_size(fig)
    if write:
        _save_fig(fig, 'entropy_distr.png')


if __name__ == '__main__':

    df = pd.read_parquet('~/tmp/entropy_X77.parquet')

    _set_style()
    # income_distr(df)
    # balances_by_account_type(df)
    # monthly_txns_by_account_type(df)
    txns_distrs(df)
