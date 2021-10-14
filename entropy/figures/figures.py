"""
Create appendix figures.

"""

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from entropy import config


def _set_style():
    plt.style.use(['seaborn-colorblind', 'seaborn-whitegrid'])


def _save_fig(fig, name):
    DPI = 1200
    fp = os.path.join(config.FIGDIR, name)
    fig.savefig(fp, dpi=DPI)
    print(f'{name} written.')

    
def income_distribution(df):
    """Plots histogram of annual incomes."""
    incomes = df.groupby(['user_id', df.date.dt.year]).income.first()
    fig = sns.displot(incomes, aspect=2)
    _save_fig(fig, 'income_distribution.png')



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

    def set_size(fig):
        fig.set_size_inches(8, 5)
        fig.tight_layout()


    data = make_data(df, account_type=['current', 'savings'], start='2015')    
    fig, ax = draw_plot(data)
    set_labels(ax)
    set_size(fig)
    if write: 
        _save_fig(fig, 'balances_by_account_type.png')


if __name__ == '__main__':

    data = pd.read_parquet('~/tmp/entropy_X77.parquet')

    _set_style()
    income_distribution(data)
    balances_by_account_type(data)
    
