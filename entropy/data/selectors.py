import re
from collections import Counter
from functools import wraps


selector_funcs = []


def selector(func):
    """Add function to list of selector functions."""
    selector_funcs.append(func)
    return func


sample_counts = Counter()


def counter(func):
    """Count sample after applying function.

    First line of func docstring is used for
    description in selection table.
    """
    @ wraps(func)
    def wrapper(*args, **kwargs):
        df = func(*args, **kwargs)
        docstr = re.match('[^\n]*', func.__doc__).group()[:-1]
        sample_counts.update({
            docstr + '@users': df.id.nunique(),
            docstr + '@accs': df.account_id.nunique(),
            docstr + '@txns': len(df),
            docstr + '@value': df.amount.abs().sum() / 1e6
        })
        return df
    return wrapper


@selector
@counter
def add_raw_count(df):
    """Raw sample.
    Add count of raw dataset to selection table."""
    return df


# @selector
# @counter
def min_number_of_months(df, min_months=6):
    """At least 6 months of data."""
    cond = df.groupby('user_id').ym.nunique() >= min_months
    users = cond[cond].index
    return df[df.user_id.isin(users)]


# @selector
# @counter
def current_account(df):
    """At least one current account."""
    mask = df.account_type.eq('current')
    users = df[mask].user_id.unique()
    return df[df.user_id.isin(users)]


# @selector
# @counter
def min_spend(df, min_txns=10, min_spend=300):
    """At least 5 monthly debits totalling GBP200.
    Drops first and last month for each user due to possible incomplete data.
    """
    data = df[['user_id', 'ym', 'amount']]
    data = data[data.amount > 0]

    # drop first and last month for each user
    g = data.groupby('user_id')
    first_month = g.ym.transform(min)
    last_month = g.ym.transform(max)
    data = data[(data.ym > first_month) & (data.ym < last_month)]

    # calculate monthly min spend and txns per user
    g = data.groupby(['user_id', 'ym']).amount
    spend = g.sum()
    txns = g.size()
    user_spend = spend.groupby('user_id').min()
    user_txns = txns.groupby('user_id').min()

    mask = (user_txns >= min_txns) & (user_spend >= min_spend)
    users = mask[mask].index
    return df[df.user_id.isin(users)]


# @selector
# @counter
def income_pmts(df):
    """Income payments in 2/3 of all observed months."""
    def helper(g):
        tot_months = g.ym.nunique()
        inc_months = g[g.tag.str.contains('_income')].ym.nunique()
        return (inc_months / tot_months) > (2/3)
    data = df[['user_id', 'transaction_date', 'tag', 'ym']]
    usrs = data.groupby('user_id').filter(helper).user_id.unique()
    return df[df.user_id.isin(usrs)]


# @selector
# @counter
def income_amount(df, lower=5_000, upper=100_000):
    """Yearly incomes between 5k and 100k.
    Yearly income calculated on rolling basis from first month of data,
    last year excluded as it has probably incomplete data.
    """
    def helper(g):
        first_month = g.transaction_date.min().strftime('%b')
        yearly_freq = 'AS-' + first_month.upper()
        year = pd.Grouper(freq=yearly_freq, key='transaction_date')
        yearly_inc = (g[g.tag.str.contains('_income')]
                      .groupby(year)
                      .amount.sum().mul(-1))
        return yearly_inc[:-1].between(lower, upper).all()
    return df.groupby('user_id').filter(helper)


# @selector
# @counter
def max_accounts(df):
    """No more than 10 active accounts in any year."""
    year = pd.Grouper(freq='M', key='transaction_date')
    usr_max = (df.groupby(['user_id', year]).account_id.nunique()
               .groupby('user_id').max())
    users = usr_max[usr_max <= 10].index
    return df[df.user_id.isin(users)]


# @selector
# @counter
def max_debits(df):
    """Debits of no more than 100k in any month."""
    month = pd.Grouper(freq='M', key='transaction_date')
    debits = df[df.amount > 0]
    usr_max = (debits.groupby(['user_id', month]).amount.sum()
               .groupby('user_id').max())
    users = usr_max[usr_max <= 100_000].index
    return df[df.user_id.isin(users)]


# @selector
# @counter
def working_age(df):
    """Working-age."""
    age = 2020 - df.year_of_birth
    return df[age.between(18, 64)]


# @selector
# @counter
def add_final_count(df):
    """Final sample.
    Add count of final dataset to selection table."""
    return df


# @selector
def returner(df):
    """Return final data and counter."""
    return df, count
