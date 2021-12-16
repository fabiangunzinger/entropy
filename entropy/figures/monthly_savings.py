import argparse
import sys

import matplotlib.pyplot as plt
import seaborn as sns

import entropy.helpers.helpers as hh
import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.figures.helpers as fh


def make_data(df, trim_pct=5):
    """Aggregates df into inflows, outflows, and net, by user month, trims at
    specified percentile, and scales flows by user's monthly income.
    """

    def trim_column_values(df, **kwargs):
        return df.apply(hd.trim, **kwargs)

    df = df.copy()
    is_not_interest_txn = ~df.tag_auto.str.contains("interest", na=False)
    is_savings_account = df.account_type.eq("savings")
    mask = is_not_interest_txn & is_savings_account
    df["debit"] = df.debit.replace({True: "sa_outflows", False: "sa_inflows"})

    return (
        df[mask]
        .groupby(["user_id", "ym", "income", "debit"])
        .amount.sum()
        .abs()
        .unstack()
        .fillna(0)
        .reset_index("income")
        .assign(
            sa_inflows=lambda df: df.sa_inflows / (df.income / 12) * 100,
            sa_outflows=lambda df: df.sa_outflows / (df.income / 12) * 100,
            sa_net_inflows=lambda df: df.sa_inflows - df.sa_outflows,
        )
        .drop(columns="income")
        .pipe(trim_column_values, pct=trim_pct)
    )


def get_xlabel(col):
    """Returns customised x-axis label for column."""
    xlabels = {
        "sa_outflows": "Outflows",
        "sa_inflows": "Inflows",
        "sa_net_inflows": "Net inflows",
    }
    return xlabels[col] + " (% of monthly income)"


def make_figure(df):
    fig, ax = plt.subplots(2, 3)
    ylabel = "User-months (%)"
    for i, col in enumerate(df.columns):
        sns.histplot(x=df[col], stat="percent", ax=ax[0, i])
        ax[0, i].set(xlabel="", ylabel=ylabel)
        non_zero = df[col] != 0
        sns.histplot(x=df[col][non_zero], stat="percent", ax=ax[1, i])
        ax[1, i].set(xlabel=get_xlabel(col), ylabel=ylabel)
    fh.set_style()
    fh.set_size(fig, height=3)
    return fig, ax


@hh.timer
def main(df):
    data = make_data(df)
    fig, ax = make_figure(data)
    return fig


if __name__ == "__main__":
    args = fh.parse_args(sys.argv[1:])
    df = ha.read_parquet(args.filepath)
    fig = main(df)
    fh.save_fig(fig, "monthly_savings.png")
