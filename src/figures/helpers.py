import argparse
import os

import matplotlib.pyplot as plt

from entropy import config


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("filepath")
    return parser.parse_args(argv)


def set_style(style=None):
    if style is None:
        style = ["seaborn-colorblind", "seaborn-whitegrid"]
    plt.style.use(style)


def set_size(fig, width=8, height=5):
    fig.set_size_inches(width, height)
    fig.tight_layout()


def set_axis_labels(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def save_fig(fig, name, dpi=300):
    fp = os.path.join(config.FIGDIR, name)
    fig.savefig(fp, dpi=dpi)
    print(f"{name} written.")

