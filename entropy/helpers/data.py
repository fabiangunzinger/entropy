import numpy as np
import pandas as pd

from IPython.display import display
import entropy.helpers.aws as ha
import entropy.helpers.helpers as hh


def order_columns(df, first=None, others_alpha=False):
    if first is None:
        order = sorted(df.columns)
    else:
        others = [c for c in df.columns if c not in first]
        order = first + sorted(others) if others_alpha else first + others
    return df.reindex(order, axis=1)


def txns_and_users(df1, df2):
    """Prints comparison of number of txns and users in df1 relative to df2."""
    txns1, users1 = len(df1), df1.user_id.nunique()
    txns2, users2 = len(df2), df2.user_id.nunique()
    txns_ratio, users_ratio = txns1 / txns2, users1 / users2
    print(
        f"df1 has {txns1:,} txns across {users1} users",
        f"({txns_ratio:.1%} and {users_ratio:.1%} of df2).",
    )


def inspect(df, nrows=2):
    print("({:,}, {})".format(*df.shape))
    display(df.head(nrows))


@hh.timer
def read_raw_data(sample='XX7', ftype='parquet', **kwargs):
    """Read MDB raw data.

    Args:
    sample: Data sample to read, one of {'777', 'X77', 'XX7'}.
    ftype: One of {'csv', 'parquet'}.

    Returns:
    Dataframe with sample raw data.
    """
    fp = f"s3://3di-data-mdb/raw/mdb_{sample}.{ftype}"
    return ha.read_parquet(fp, **kwargs)


@hh.timer
def read_txn_data(sample='XX7', **kwargs):
    fp = f"s3://3di-project-entropy/txn_{sample}.parquet"
    return ha.read_parquet(fp, **kwargs)


@hh.timer
def read_analysis_data(sample='XX7', **kwargs):
    fp = f"s3://3di-project-entropy/analysis_{sample}.parquet"
    return ha.read_parquet(fp, **kwargs)


@hh.timer
def read_logins(**kwargs):
    fp = "s3://3di-data-mdb/raw/20200630_UserLoginsForNeedham.csv"
    return ha.read_csv(fp, names=["user_id", "date"], parse_dates=["date"], **kwargs)


def trim(series, pct=1, how="both"):
    """Replaces series values outside of specified percentile on both sides with nan.

    Arguments:
        pct : Percentile of data to be removed from specified ends.
            Default is 1.
        how: end(s) of distribution from which to trim values. One of
            {'both', 'lower', 'upper'}. Defaults to 'both'.

    """
    lower, upper = np.nanpercentile(series, [pct, 100 - pct])
    if how == "both":
        cond = series.between(lower, upper)
    elif how == "lower":
        cond = series.gt(lower)
    else:
        cond = series.lt(upper)
    return series.where(cond, np.nan)


def winsorise(series, pct=1, how="both"):
    """Replaces series outside of specified percentile with percentile
    value."""
    lower_pct, upper_pct = np.nanpercentile(series, [pct, 100 - pct])
    if how == "both":
        kwargs = dict(lower=lower_pct, upper=upper_pct)
    elif how == "lower":
        kwargs = dict(lower=lower_pct)
    else:
        kwargs = dict(upper=upper_pct)
    return series.clip(**kwargs)


def breakdown(df, group_var, group_var_value, component_var, metric="value", net=False):
    """Calculates sorted breakdown of group_var_value by component_var.

    Args:
      metric:
        "value" calculates amount spent on components, "counts" the number of
        transactions per component.
      net:
        Boolean indicating whether, if metric is "value", net or gross amounts
        are calculated. Defaults to False, which produces gross amounts.
    """
    return (
        df[df[group_var].eq(group_var_value)]
        .assign(amount=lambda df: df.amount if net else df.amount.abs())
        .groupby(component_var)
        .amount.agg("sum" if metric == "value" else "count")
        .replace(0, np.nan)
        .dropna()
        .sort_values()
    )


def pat_in_col(df, pat, col):
    """Returns rows for which col contains pattern."""
    return df[df[col].str.contains(pat, na=False)]


def user_period_data(df, user_id, period):
    idx = pd.IndexSlice
    return (
        df.set_index(["user_id", "date"], drop=False)
        .loc[idx[user_id, period], :]
        .reset_index(drop=True)
    )


def user_data(df, user_id):
    return df[df.user_id.eq(user_id)]
