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
        f"({txns_ratio:.1%} and {users_ratio:.1%} of df2)."
    )


def inspect(df, nrows=2):
    print("({:,}, {})".format(*df.shape))
    display(df.head(nrows))


@hh.timer
def read_data(sample):
    fp = f"s3://3di-project-entropy/entropy_{sample}.parquet"
    return ha.read_parquet(fp)


def load_samples(samples):
    return (read_data(sample) for sample in samples)


def trim(series, pct=1):
    """Replaces series values outside of specified percentile on both sides with nan."""
    lower, upper = np.nanpercentile(series, [pct, 100 - pct])
    return series.where(series.between(lower, upper), np.nan)
