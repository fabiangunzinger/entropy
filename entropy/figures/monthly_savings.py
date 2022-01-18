import argparse
import functools
import sys

import matplotlib.pyplot as plt
import seaborn as sns

import entropy.helpers.helpers as hh
import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.figures.helpers as fh


def monthly_savings(df):
    """Plots histograms of savings account flows."""
    pct_histplot = functools.partial(sns.histplot, stat='percent')
    columns = ['sa_scaled_inflows', 'sa_scaled_outflows', 'sa_scaled_net_inflows']
    xlabels = {
        "sa_scaled_outflows": "Outflows (% of monthly income)",
        "sa_scaled_inflows": "Inflows (% of monthly income)",
        "sa_scaled_net_inflows": "Net inflows (% of monthly income)",
    }
    ylabel = "User-months (%)"

    fig, ax = plt.subplots(2, 3)
    for i, col in enumerate(columns):
        data = df[col].pipe(hd.trim, pct=1, how='both')
        pct_histplot(x=data, ax=ax[0, i])
        ax[0, i].set(xlabel="", ylabel=ylabel)
        data = data[data != 0]
        pct_histplot(x=data, ax=ax[1, i])
        ax[1, i].set(xlabel=xlabel(col), ylabel=ylabel)
    fh.set_style()
    fh.set_size(fig, height=3)
    return fig, ax


# if __name__ == "__main__":
#     args = fh.parse_args(sys.argv[1:])
#     df = ha.read_parquet(args.filepath)
#     fig = main(df)
#     fh.save_fig(fig, "monthly_savings.png")
