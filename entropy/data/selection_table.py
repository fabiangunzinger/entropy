import os
import pandas as pd

from entropy import config


def make_selection_table(dict):
    """Create sample selection table for data appendix."""
    df = pd.DataFrame(dict.items(), columns=["step", "counts"])
    df[["step", "metric"]] = df.step.str.split("@", expand=True)

    df = (
        df.groupby(["step", "metric"], sort=False)
        .counts.sum()
        .unstack("metric")
        .rename_axis(columns=None)
        .reset_index()
    )

    ints = ['users', 'user_months', 'accounts', 'txns']
    df[ints] = df[ints].applymap('{:,.0f}'.format)

    df.columns = [
        "",
        "Users",
        "User-months",
        "Accounts",
        "Transactions",
    ]
    return df


def write_selection_table(table, sample):
    """Export sample selection table in Latex format."""
    filename = f"sample_selection_{sample}.tex"
    filepath = os.path.join(config.TABDIR, filename)
    latex_table = table.to_latex(index=False, escape=False, column_format="lrrrr")
    with pd.option_context("max_colwidth", None):
        with open(filepath, "w") as f:
            f.write(latex_table)
