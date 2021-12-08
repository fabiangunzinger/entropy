import sys

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

import entropy.helpers.aws as ha
import entropy.figures.helpers as fh


def user_age_hist(df):
    """Plots histogram of user ages."""

    def make_data(df):
        return 2021 - df.groupby("user_id").user_yob.first()

    def make_figure(data):
        fig, ax = plt.subplots()
        bins = np.linspace(20, 65, 46)
        sns.histplot(data, bins=bins - 0.5)
        return fig, ax

    data = make_data(df)
    fig, ax = make_figure(data)
    fh.set_style()
    fh.set_size(fig)
    fh.set_axis_labels(ax, xlabel="Age", ylabel="Number of users")
    return fig


if __name__ == "__main__":
    args = fh.parse_args(sys.argv[1:])
    df = ha.read_parquet(args.filepath)
    fig = user_age_hist(df)
    fh.save_fig(fig, "user_age_hist.png")
