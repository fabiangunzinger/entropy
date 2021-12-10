import argparse
import sys

import matplotlib.pyplot as plt
import seaborn as sns

import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.figures.helpers as fh


def trim_column_values(df, **kwargs):
    return df.apply(hd.trim, **kwargs)


def make_data(df, trim_pct=5):
    """Aggregates df into inflows, outflows, and net, by user month, trims at
    specified percentile, and scales flows by user's monthly income.
    """
    mask = df.account_type.eq("savings") & ~df.tag_auto.str.contains(
        "interest", na=False
    )
    df["debit"] = df.debit.replace({True: "debit", False: "credit"})
    return (
        df[mask]
        .groupby(["user_id", "ym", "income", "debit"])
        .amount.sum()
        .abs()
        .unstack()
        .reset_index("income")
        .assign(
            credit=lambda df: df.credit / (df.income / 12) * 100,
            debit=lambda df: df.debit / (df.income / 12) * 100,
            net=lambda df: df.credit - df.debit,
        )
        .drop(columns="income")
        .pipe(trim_column_values, pct=trim_pct)
    )


def get_xlabel(col):
    """Returns customised x-axis label for column."""
    xlabels = {
        "debit": "Outflows",
        "credit": "Inflows",
        "net": "Net flows",
    }
    return xlabels[col] + " % of monthly income"


def make_figure(df):
    fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    ylabel = "User-months (%)"
    for i, col in enumerate(df.columns):
        sns.histplot(x=df[col], stat="percent", ax=ax[i])
        ax[i].set(xlabel=get_xlabel(col), ylabel=ylabel)
    return fig, ax


def monthly_savings(df):
    data = make_data(df)
    fig, ax = make_figure(data)
    fh.set_style()
    fh.set_size(fig)
    return fig


if __name__ == "__main__":
    args = fh.parse_args(sys.argv[1:])
    df = ha.read_parquet(args.filepath)
    fig = monthly_savings(df)
    fh.save_fig(fig, "monthly_savings.png")
