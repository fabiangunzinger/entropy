from collections import Counter
from functools import wraps
import re


count = Counter()
cleaner_funcs = []
selector_funcs = []


def cleaner(func):
    """Add function to list of cleaner functions."""
    cleaner_funcs.append(func)
    return func


def selector(func):
    """Add function to list of selector functions."""
    selector_funcs.append(func)
    return func


def counter(func):
    """Count sample after each selection function.

    First line of func docstring is used for
    description in selection table.
    """
    @ wraps(func)
    def wrapper(*args, **kwargs):
        df = func(*args, **kwargs)
        docstr = re.match('[^\n]*', func.__doc__).group()[:-1]
        count.update({docstr + '@users': df.id.nunique(),
                      docstr + '@accs': df.account_id.nunique(),
                      docstr + '@txns': len(df),
                      docstr + '@value': df.amount.abs().sum() / 1e6})
        return df
    return wrapper
