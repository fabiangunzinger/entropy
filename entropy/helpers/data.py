import numpy as np


def trim(series, pct=1):
    """Replaces series values outside of specified percentile on both sides with nan."""
    lower, upper = np.nanpercentile(series, [pct, 100 - pct])
    return series.where(series.between(lower, upper), np.nan)


