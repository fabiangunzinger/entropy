import numpy as np

from IPython.display import display
import entropy.helpers.aws as ha
import entropy.helpers.helpers as hh


def inspect(df, nrows=2):
    print('({:,}, {})'.format(*df.shape))
    display(df.head(nrows))
    

@hh.timer
def read_data(sample):
    fp = f's3://3di-project-entropy/entropy_{sample}.parquet'
    return ha.read_parquet(fp)


def load_samples(samples):
    return (read_data(sample) for sample in samples)


def trim(series, pct=1):
    """Replaces series values outside of specified percentile on both sides with nan."""
    lower, upper = np.nanpercentile(series, [pct, 100 - pct])
    return series.where(series.between(lower, upper), np.nan)


