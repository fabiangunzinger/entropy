import numpy as np

from IPython.display import display
import entropy.helpers.aws as ha
import entropy.helpers.helpers as hh


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
def read_analysis_data(sample='XX7'):
    fp = f's3://3di-project-entropy/analysis_data_{sample}.parquet'
    return ha.read_parquet(fp)

@hh.timer
def read_sample(sample):
    fp = f"s3://3di-project-entropy/entropy_{sample}.parquet"
    return ha.read_parquet(fp)


def read_samples(samples):
    return (read_sample(sample) for sample in samples)


def trim(series, pct=1, how='both'):
    """Replaces series values outside of specified percentile on both sides with nan.
    
    Arguments:
        pct : Percentile of data to be removed from specified ends.
            Default is 1.
        how: end(s) of distribution from which to trim values. One of
            {'both', 'lower', 'upper'}. Defaults to 'both'.

    """
    lower, upper = np.nanpercentile(series, [pct, 100 - pct])
    if how == 'both':
        cond = series.between(lower, upper)
    elif how == 'lower':
        cond = series.gt(lower)
    else:
        cond = series.lt(upper)
    return series.where(cond, np.nan)


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


def colname_subset(df, pattern):
    """Returns names of all columns that contain pattern."""
    columns = df.columns
    return list(columns[columns.str.contains(pattern)])

