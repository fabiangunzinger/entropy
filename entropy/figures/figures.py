"""
Create all figures.

Approach:
1. Load main dataset and produce all figures from it.
2. One function per figure, which produces data used in figure and figure
itself.
3. Use styling helpers across functions whenever possible.

"""
import argparse
import functools
import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from entropy import config
from entropy.helpers import aws


paper_figures = []

def paper_figure(func):
    paper_figures.append(func)
    return func


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    return parser.parse_args(argv)


def _set_style():
    plt.style.use(["seaborn-colorblind", "seaborn-whitegrid"])


def _set_size(fig):
    fig.set_size_inches(8, 5)
    fig.tight_layout()


def _set_axis_labels(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def _save_fig(fig, name):
    dpi = 300
    fp = os.path.join(config.FIGDIR, name)
    fig.savefig(fp, dpi=dpi)
    print(f"{name} written.")


@paper_figure
def user_age_hist(df, write=True):
    """Plots histogram of user ages."""
    def make_data(df):
        return 2021 - df.groupby('user_id').user_yob.first()

    def make_plot(data):
        fig, ax = plt.subplots()
        bins = np.linspace(20, 65, 46)
        sns.histplot(data, bins=bins - 0.5)
        return fig, ax
    
    data = make_data(df)
    fig, ax = make_plot(data)
    _set_style()
    _set_size(fig)
    _set_axis_labels(ax, xlabel='Age', ylabel='Number of users')
    if write:
        _save_fig(fig, 'user_age_hist.png')


@paper_figure
def user_income_hist(df, write=True):
    """Plots histogram of annual user incomes."""
    from matplotlib.ticker import StrMethodFormatter

    def make_data(df):
        incomes = df.groupby(["user_id", df.date.dt.year]).income.first()
        return incomes[incomes.between(0, 150_000)]

    def draw_plot(df):
        fix, ax = plt.subplots()
        ax = sns.histplot(df)
        return fix, ax

    def set_xtick_labels(ax):
        ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))

    data = make_data(df)
    fig, ax = draw_plot(data)
    _set_style()
    _set_size(fig)
    _set_axis_labels(ax, "Yearly income (£)", "Number of users")
    set_xtick_labels(ax)
    if write:
        _save_fig(fig, "user_income_hist.png")


def balances_by_account_type(df, write=True, **kwargs):
    def make_data(df, account_type, freq="w", agg="median", start=None, end=None):
        """Returns user balances at specified freq by account type."""
        return (
            df.loc[df.account_type.isin(account_type)]
            # single daily balance for each account
            .set_index("date")
            .groupby(["account_type", "account_id"])
            .resample("d")
            .balance.first()
            # median daily balance per account type
            .groupby(["date", "account_type"])
            .median()
            # one column per account type with legend labels
            .unstack()
            .rename(columns=lambda x: " ".join([x.title(), "accounts"]))
            .rename_axis(columns=lambda x: x.replace("_", " ").title())
            .resample(freq)
            .agg(agg)
            .loc[start:end]
        )

    def draw_plot(df):
        linestyles = [k for k, v in mpl.lines.lineStyles.items()]
        markers = [k for k, v in mpl.markers.MarkerStyle.markers.items()]
        fig, ax = plt.subplots()
        for i, col in enumerate(df):
            ax.plot(df[col], label=col, linestyle=linestyles[i])
        ax.legend(title=df.columns.name)
        return fig, ax

    data = make_data(df, account_type=["current", "savings"], **kwargs)
    fig, ax = draw_plot(data)
    _set_axis_labels(ax, "Year", "Median account balance (£)")
    _set_size(fig)
    if write:
        _save_fig(fig, "balances_by_account_type.png")


@paper_figure
def num_txns_by_account_type(df, write=True):
    """Plots boxenplot with number of monthly transactions by account type."""
    def make_data(df):
        mask = df.account_type.isin(['current', 'credit card', 'savings'])
        return (
            df.loc[mask]
            .set_index("date")
            .groupby(["account_type", "account_id"], observed=True)
            .resample("M")
            .id.count()
            .rename("num_txns")
            .reset_index()
        )

    def make_plot(df):
        fig, ax = plt.subplots()
        order = ['current', 'credit card', 'savings']
        ax = sns.boxenplot(data=df, x="num_txns", y="account_type", order=order)
        return fig, ax

    def set_ytick_labels(ax):
        # capitalise first letter of, and add 'account' suffix to, ytick labels
        to_label = lambda x: " ".join([x[0].upper() + x[1:], "accounts"])
        ytick_labels = [to_label(i.get_text()) for i in ax.get_yticklabels()]
        ax.set_yticklabels(ytick_labels)

    fig, ax = make_plot(make_data(df))
    set_ytick_labels(ax)
    _set_axis_labels(ax, xlabel="Number of transactions per month", ylabel="")
    _set_size(fig)
    if write:
        _save_fig(fig, "num_txns_by_account_type.png")


@paper_figure
def txns_categories_entropy_hists(df, write=True):
    """Plots histogram of number of user-month txns and spending categories,
    and user-month entropy."""

    def make_txns_hist(g):
        data = g.id.count()
        histplot(data=data, bins=20, ax=ax[0])
        ax[0].set(xlabel="Transactions", ylabel=ylabel)

    def make_spend_cat_hist(g):
        data = g.tag.nunique()
        bins = np.arange(df.tag.nunique() + 1) - 0.5
        histplot(data=data, bins=bins, ax=ax[1])
        ax[1].set(xlabel="Spending categories", ylabel=ylabel)

    def make_entropy_hist(g):
        data = g.entropy_tag.first()
        histplot(data=data, bins=20, ax=ax[2])
        ax[2].set(xlabel="Entropy", ylabel=ylabel)

    def set_size(fig):
        fig.set_size_inches(8, 2.5)
        fig.tight_layout()

    g = df.set_index("date").groupby("user_id").resample("M")
    histplot = functools.partial(sns.histplot, stat="percent")
    ylabel = "User-months (%)"

    fig, ax = plt.subplots(1, 3)
    make_txns_hist(g)
    make_spend_cat_hist(g)
    make_entropy_hist(g)
    set_size(fig)
    if write:
        _save_fig(fig, "txns_categories_entropy_hists.png")


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)
    df = aws.read_parquet(args.filepath)
    for figure in paper_figures:
        figure(df)


if __name__ == "__main__":
    main()

