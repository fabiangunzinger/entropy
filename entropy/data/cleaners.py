import re
import numpy as np
from entropy.data import helpers


cleaner_funcs = []


def cleaner(func):
    """Adds function to list of cleaner functions."""
    cleaner_funcs.append(func)
    return func


@cleaner
def rename_cols(df):
    """Renames columns where needed.

    Each variable in the data pertains either to a txn, a user,
    or an account, and is prepended by an appropriate prefix,
    except, for brevity, txn variables, which have no prefix
    (e.g `txn_id` is `id`).
    """
    new_names = {
        'Account Created Date': 'account_created',
        'Account Reference': 'account_id',
        'Derived Gender': 'user_gender',
        'LSOA': 'user_lsoa',
        'MSOA': 'user_msoa',
        'Merchant Name': 'merchant',
        'Postcode': 'user_postcode',
        'Provider Group Name': 'account_provider',
        'Salary Range': 'user_salary_range',
        'Transaction Date': 'date',
        'Transaction Description': 'desc',
        'Transaction Reference': 'id',
        'Transaction Updated Flag': 'updated_flag',
        'User Reference': 'user_id',
        'Year of Birth': 'user_yob',
        'Auto Purpose Tag Name': 'tag_auto',
        'Manual Tag Name': 'tag_manual',
        'User Precedence Tag Name': 'tag_up',
        'Latest Recorded Balance': 'latest_balance',
    }
    return df.rename(columns=new_names)


@cleaner
def drop_last_month(df):
    """Drops last month.
    Might have missing data. For first month, Jan 2012, we have complete data.
    """
    ym = df.date.dt.to_period('M')
    return df[ym < ym.max()]


@cleaner
def drop_unneeded_vars(df):
    vars = ['user_lsoa', 'user_msoa']
    return df.drop(columns=vars)


@cleaner
def clean_headers(df):
    """Turns column headers into snake case."""
    df.columns = (df.columns
                  .str.lower()
                  .str.replace(r'[\s\.]', '_', regex=True)
                  .str.strip())
    return df


@cleaner
def lowercase_categories(df):
    """Converts all category values to lowercase to simplify regex searcher."""
    cats = df.select_dtypes('category').columns
    df[cats] = (df[cats]
                .astype('str')
                .apply(lambda x: x.str.lower())
                .astype('category'))
    return df


@cleaner
def order_salaries(df):
    """Orders salary category variable."""
    cats = ['< 10k', '10k to 20k', '20k to 30k',
            '30k to 40k', '40k to 50k', '50k to 60k',
            '60k to 70k', '70k to 80k', '> 80k']
    df['user_salary_range'] = (df.user_salary_range
                               .cat.set_categories(cats, ordered=True))
    return df


@cleaner
def gender_to_female(df):
    """Replaces gender variable with female dummy."""
    df['user_female'] = df.user_gender == 'f'
    df['user_female'] = df.user_female.where(df.user_gender != 'u')
    return df.drop(columns='user_gender')


@cleaner
def credit_debit_to_debit(df):
    """Replaces credit_debit variable with credit dummy."""
    df['debit'] = df.credit_debit == 'debit'
    return df.drop(columns='credit_debit')


@cleaner
def sign_amount(df):
    """Makes credits negative."""
    df['amount'] = df.amount.where(df.debit, df.amount.mul(-1))
    return df


@cleaner
def missings_to_nan(df):
    """Converts missing category values to NaN."""
    mbl = 'merchant_business_line'
    mbl_missing = ['no merchant business line', 'unknown merchant']
    df[mbl] = df[mbl].cat.remove_categories(mbl_missing)     
    df['merchant'] = df['merchant'].cat.remove_categories(['no merchant'])
    df['tag_up'] = df['tag_up'].cat.remove_categories(['no tag'])
    df['tag_auto'] = df['tag_auto'].cat.remove_categories(['no tag'])
    df['tag_manual'] = df['tag_manual'].cat.remove_categories(['no tag'])
    return df


@cleaner
def zero_balances_to_missing(df):
    """Replaces zero latest balances with missings.

    Latest balance column refers to account balance at last account
    refresh date. Exact zero values are likely due to unsuccessful
    account refresh (see data dictionary) and thus treated as missing.
    """
    df['latest_balance'] = df.latest_balance.replace(0, np.nan)
    return df


@cleaner
def tag_transfers(df):
    """Tags untagged tranfsers."""
    tfr_strings = [' ft', ' trf', 'xfer', 'transfer']
    exclude_strings = ['fee', 'interest', 'rewards']

    tfr_pattern = '|'.join(tfr_strings)
    exclude_pattern = '|'.join(exclude_strings)
    mask = (df.desc.str.contains(tfr_pattern)
            & ~df.desc.str.contains(exclude_pattern)
            & df.tag_auto.isna())

    df.loc[mask, 'tag_auto'] = 'transfers'
    return df


def _apply_grouping(grouping, df, col_name):
    """Applies grouping to col_name in dataframe in-place.

    Args:
      grouping: a dict with name-tags pairs, where name
        is the group name that will be applied to each txn
        for which tag_auto equals one of the tags.
      col_name: a column from df into which the group
        names will be stored.
    """
    for group, tags in grouping.items():
        escaped_tags = [re.escape(tag) for tag in tags]
        pattern = '|'.join(escaped_tags)
        mask = df.tag_auto.str.fullmatch(pattern, na=False)
        df.loc[mask, col_name] = group

    return df


@cleaner
def add_tag_group(df):
    """Groups transactions into income, spend, and transfers."""
    df['tag_group'] = np.nan
    _apply_grouping(helpers.tag_groups, df, 'tag_group')
    return df


@cleaner
def add_tag(df):
    """Creates custom transaction tag."""
    df['tag'] = np.nan
    _apply_grouping(helpers.lloyds_spend, df, 'tag')
    _apply_grouping(helpers.hacioglu_income, df, 'tag')
    _apply_grouping(helpers.custom_transfers, df, 'tag')
    return df


@cleaner
def correct_tag_up(df):
    """Ensures user precedence tag is defined as in data dictionary.

    tag_up is defined as equalling tag_manual if tag_manual not missing else
    tag_auto. This definition is violated in two ways in the data: sometimes
    tag_up is missing while one of the other two tags isn't, sometimes tag_up is
    not missing but both other tags are. In the latter case, we leave tag_up
    unchanged.
    """
    correct_up_value = (df.tag_manual
                        .astype('object')
                        .fillna(df.tag_auto)
                        .astype('category'))

    df['tag_up'] = (df.tag_up
                    .astype('object')
                    .where(df.tag_up.notna(), correct_up_value)
                    .astype('category'))
    return df


@cleaner
def add_year_month_variable(df):
    """Creates year-month date as helper variable."""
    y = df.date.dt.year * 100
    m = df.date.dt.month
    df['ym'] = y + m
    return df


@cleaner
def order_and_sort(df):
    """Orders columns and sort values."""
    cols = df.columns
    first = ['id', 'date', 'user_id', 'amount', 'desc', 'merchant',
             'tag_group', 'tag']    
    user = cols[cols.str.startswith('user') & ~cols.isin(first)]
    account = cols[cols.str.startswith('account') & ~cols.isin(first)]
    txn = cols[~cols.isin(user.append(account)) & ~cols.isin(first)]    
    order = first + sorted(user) + sorted(account) + sorted(txn)

    return df[order].sort_values(['user_id', 'date'])


