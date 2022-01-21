import argparse
import functools
import os
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import s3fs

import entropy.helpers.helpers as hh
import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.figures.helpers as fh


figure_funcs = []


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--fig", type=str, help="Function name of figure to create.")
    return parser.parse_args(argv)


def sample_description(df, write=True):
    """Creates a 2x2 figure with basic user demographic info."""
    figname = "sample_description.png"
    colour = "blue"
    g = df.groupby("user_id")
    fig, ax = plt.subplots(2, 2)

    data = g.age.first()
    bins = np.linspace(20, 65, 46) - 0.5
    sns.histplot(data, bins=bins, color=colour, ax=ax[0, 0])
    fh.set_axis_labels(ax[0, 0], "Age", "Number of users")

    data = g.income.last()
    sns.histplot(data, color=colour, ax=ax[0, 1])
    ax[0, 1].xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter("{x:,.0f}"))
    fh.set_axis_labels(ax[0, 1], "Income (£)", "Number of users")

    data = df.groupby("user_id").region.first().value_counts(ascending=True)
    data.plot(kind="barh", color=colour, ax=ax[1, 0])
    fh.set_axis_labels(ax[1, 0], "Number of users", "")

    gender_names = {1: "Female", 0: "Male"}
    data = g.user_female.first().map(gender_names).value_counts()
    data.plot(kind="bar", color=colour, rot=0, ax=ax[1, 1])
    fh.set_axis_labels(ax[0, 1], "", "Number of users")

    fh.set_style()
    fh.set_size(fig)
    if write:
        fh.save_fig(fig, figname)


def num_txns_by_account_type(df, write=True):
    """Plots boxenplot with number of monthly transactions by account type."""

    def make_data(df):
        mask = df.account_type.isin(["current", "credit card", "savings"])
        return (
            df.loc[mask]
            .set_index("date")
            .groupby(["account_type", "account_id"], observed=True)
            .resample("M")
            .id.count()
            .rename("num_txns")
            .reset_index()
        )

    def make_figure(df):
        fig, ax = plt.subplots()
        order = ["current", "credit card", "savings"]
        ax = sns.boxenplot(data=df, x="num_txns", y="account_type", order=order)
        return fig, ax

    def set_ytick_labels(ax):
        # capitalise first letter of, and add 'account' suffix to, ytick labels
        to_label = lambda x: " ".join([x[0].upper() + x[1:], "accounts"])
        ytick_labels = [to_label(i.get_text()) for i in ax.get_yticklabels()]
        ax.set_yticklabels(ytick_labels)

    fig, ax = make_figure(make_data(df))
    set_ytick_labels(ax)
    fh.set_axis_labels(ax, xlabel="Number of transactions per month", ylabel="")
    fh.set_size(fig)
    if write:
        fh.save_fig(fig, "num_txns_by_account_type.png")


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
    fh.set_axis_labels(ax, "Year", "Median account balance (£)")
    fh.set_size(fig)
    if write:
        fh.save_fig(fig, "balances_by_account_type.png")


def txns_breakdowns_and_entropy(df, write=True):
    """Plots histogram of number of user-month txns and spending categories,
    and user-month entropy."""

    def make_data(df):
        return df[df.tag_group.eq("spend")]

    def make_figure(data):
        histplot = functools.partial(sns.histplot, stat="percent")
        ylabel = "User-months (%)"
        user_month_data = data.set_index("date").groupby("user_id").resample("m")

        fig, ax = plt.subplots(2, 2)

        axis = ax[0, 0]
        d = user_month_data.id.count()
        d = ha.trim(d, pct=1)
        median = d.median()
        histplot(data=d, bins=30, ax=axis)
        axis.axvline(median, color="green")
        axis.text(median + 5, 8, f"Median: {median:.0f}")
        fh.set_axis_labels(axis, "Transactions", ylabel)

        axis = ax[0, 1]
        (
            data.tag.str.replace("_", " ")
            .str.title()
            .value_counts(ascending=True, normalize=True)
            .mul(100)[-9:]
            .plot(kind="barh", ax=axis)
        )
        fh.set_axis_labels(axis, "Transactions (%)", "Spending categories")

        axis = ax[1, 0]
        d = user_month_data.tag.nunique()
        bins = np.arange(9 + 1) + 0.5
        histplot(data=d, bins=bins, ax=axis)
        fh.set_axis_labels(axis, "Number of spending categories", ylabel)

        axis = ax[1, 1]
        d = user_month_data.entropy_sptac.first()
        histplot(data=d, bins=40, ax=axis)
        fh.set_axis_labels(axis, "Entropy", ylabel)

        return fig, ax

    data = make_data(df)
    fig, ax = make_figure(data)
    fh.set_style()
    fh.set_size(fig)
    if write:
        fh.save_fig(fig, "txns_breakdowns_and_entropy.png")


def monthly_savings(df):
    """Plots histograms of savings account flows."""
    pct_histplot = functools.partial(sns.histplot, stat="percent")
    columns = ["sa_scaled_inflows", "sa_scaled_outflows", "sa_scaled_net_inflows"]
    xlabels = {
        "sa_scaled_outflows": "Outflows (% of monthly income)",
        "sa_scaled_inflows": "Inflows (% of monthly income)",
        "sa_scaled_net_inflows": "Net inflows (% of monthly income)",
    }
    ylabel = "User-months (%)"

    fig, ax = plt.subplots(2, 3)
    for i, col in enumerate(columns):
        data = df[col].pipe(hd.trim, pct=1, how="both")
        pct_histplot(x=data, ax=ax[0, i])
        ax[0, i].set(xlabel="", ylabel=ylabel)
        data = data[data != 0]
        pct_histplot(x=data, ax=ax[1, i])
        ax[1, i].set(xlabel=xlabels[col], ylabel=ylabel)
    fh.set_style()
    fh.set_size(fig, height=3)
    return fig, ax


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = parse_args(argv)




# if __name__ == "__main__":
# def main(argv=None):
#     if argv is None:
#         argv = sys.argv[1:]
#     args = parse_args(argv)
#     df = aws.read_parquet(args.filepath)
#     for figure in paper_figures:
#         figure(df)
#     main()
