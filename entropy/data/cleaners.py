import numpy as np


cleaner_funcs = []


def cleaner(func):
    """Add function to list of cleaner functions."""
    cleaner_funcs.append(func)
    return func


@cleaner
def rename_cols(df):
    """Rename columns where needed.

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
    }
    return df.rename(columns=new_names)


@cleaner
def drop_unneeded_vars(df):
    vars = ['user_lsoa', 'user_msoa', 'updated_flag']
    return df.drop(columns=vars)


@cleaner
def clean_headers(df):
    """Turn column headers into snake case."""
    df.columns = (df.columns
                  .str.lower()
                  .str.replace(r'[\s\.]', '_', regex=True)
                  .str.strip())
    return df


@cleaner
def lowercase_categories(df):
    """Convert all category values to lowercase to simplify regex searcher."""
    cats = df.select_dtypes('category').columns
    df[cats] = (df[cats]
                .astype('str')
                .apply(lambda x: x.str.lower())
                .astype('category'))
    return df


@cleaner
def order_salaries(df):
    """Order salary category variable."""
    cats = ['< 10k', '10k to 20k', '20k to 30k',
            '30k to 40k', '40k to 50k', '50k to 60k',
            '60k to 70k', '70k to 80k', '> 80k']
    df['user_salary_range'] = (df.user_salary_range
                               .cat.set_categories(cats, ordered=True))
    return df


@cleaner
def gender_to_female(df):
    """Replace gender variable with female dummy."""
    df['user_female'] = df.user_gender == 'f'
    df['user_female'] = df.user_female.where(df.user_gender != 'u')
    return df.drop(columns='user_gender')


@cleaner
def credit_debit_to_debit(df):
    """Replace credit_debit variable with credit dummy."""
    df['debit'] = df.credit_debit == 'debit'
    return df.drop(columns='credit_debit')


@cleaner
def sign_amount(df):
    """Make credits negative."""
    df['amount'] = df.amount.where(df.debit, df.amount.mul(-1))
    return df


@cleaner
def missings_to_nan(df):
    """Convert missing category values to NaN."""
    mbl = 'merchant_business_line'
    mbl_missing = ['no merchant business line', 'unknown merchant']
    df[mbl] = df[mbl].cat.remove_categories(mbl_missing)     
    df['merchant'] = df['merchant'].cat.remove_categories(['no merchant'])
    df['tag_up'] = df['tag_up'].cat.remove_categories(['no tag'])
    df['tag_auto'] = df['tag_auto'].cat.remove_categories(['no tag'])
    df['tag_manual'] = df['tag_manual'].cat.remove_categories(['no tag'])
    return df


@cleaner
def correct_tag_up(df):
    """Set tag_up to tag_manual if tag_manual not missing else to tag_auto.
    
    This definition of tag_up is violated in two ways: sometimes tag_up is
    missing while one of the other two tags isn't, sometimes tag_up is
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
def add_tag(df):
    """Create empty tag variable for custom categories."""
    df['tag'] = np.nan
    return df


@cleaner
def tag_incomes(df):
    """Tag earnings, pensions, benefits, and other income.
    Based on Appendix A in Haciouglu et al. (2020).
    """
    incomes = {
        'earnings': [
            'salary or wages - main',
            'salary or wages - other',
            'salary - secondary',
        ],
        'pensions': [
            'pension - other',
            'pension',
            'work pension',
            'state pension',
            'pension or investments',
        ],
        'benefits': [
            'benefits',
            'family benefits',
            'job seekers benefits',
            'other benefits',
            'incapacity benefits'
        ],
        'other': [
            'rental income - whole property',
            'rental income - room',
            'rental income',
            'irregular income or gifts',
            'miscellaneous income - other',
            'investment income - other',
            'loan or credit income',
            'bond income',
            'interest income',
            'dividend',
            'student loan funds',
        ],
    }

    for type, tags in incomes.items():
        pattern = '|'.join(tags)
        mask = df.tag_up.str.match(pattern) & ~df.debit
        df.loc[mask, 'tag'] = type + '_income'

    return df


@cleaner
def fill_tag(df):
    """Fill empty tags with user-precedence tag convert to category."""
    df['tag'] = df.tag.where(df.tag.notna(), df.tag_up).astype('category')
    return df


@cleaner
def add_variables(df):
    """Create helper variables."""
    y = df.date.dt.year * 100
    m = df.date.dt.month
    df['ym'] = y + m
    return df


@cleaner
def order_and_sort(df):
    """Order columns and sort values."""
    cols = df.columns
    first = ['id', 'date', 'user_id', 'amount', 'desc', 'merchant', 'tag_up']    
    user = cols[cols.str.startswith('user') & ~cols.isin(first)]
    account = cols[cols.str.startswith('account') & ~cols.isin(first)]
    txn = cols[~cols.isin(user.append(account)) & ~cols.isin(first)]    
    order = first + sorted(user) + sorted(account) + sorted(txn)

    return df[order].sort_values(['user_id', 'date'])


# @cleaner
def tag_pmt_pairs(df, knn=5):
    """Tag payments from one account to another as transfers.

    Identification criteria:
    1. same user
    2. larger than GBP50
    3. same amount
    4. no more than 4 days apart
    5. of the opposite sign (debit/credit)
    6. not already part of another transfer pair. This can happen in two ways:
       - A txn forms a pair with two neighbours at different distances,
         addressed in <1>.
       - A txn forms a pair with a neighbour and the neighbour with one
         of its own neighbours, addressed in <2>.

    Code sorts data by user, amount, and transaction date, and checks for each
    txn and each of its k nearest preceeding neighbours whether, together, they
    meet the above criteria.
    """
    df['amount'] = df.amount.abs()
    df = df.sort_values(['user_id', 'amount', 'transaction_date'])
    for k in range(1, knn+1):
        meets_conds = (
            (df.user_id.values == df.user_id.shift(k).values)
            & (df.amount.values > 50)
            & (df.amount.values == df.amount.shift(k).values)
            & (df.transaction_date.diff(k).dt.days.values <= 4)
            & (df.credit_debit.values != df.credit_debit.shift(k).values)
            & (df.tag.values != 'transfers')                       # <1>
            & (df.tag.shift(k).values != 'transfers')              # <1>
        )
        # tag first txn of pair
        neighbr_meets_cond = np.roll(meets_conds, k)
        neighbr_meets_cond[:k] = False
        is_tfr = meets_conds & ~neighbr_meets_cond                 # <2>
        df['tag'] = np.where(is_tfr, 'transfers', df.tag)
        # tag second txn of pair
        mask = np.roll(meets_conds, -k)
        mask[-k:] = False
        df['tag'] = np.where(mask, 'transfers', df.tag)
    return df


# @cleaner
def tag_transfers(df):
    """Tag txns with description indicating tranfser payment."""
    tfr_strings = [' ft', ' trf', 'xfer', 'transfer']
    exclude = ['fee', 'interest']
    mask = (df.transaction_description.str.contains('|'.join(tfr_strings))
            & ~df.transaction_description.str.contains('|'.join(exclude)))
    df.loc[mask, 'tag'] = 'transfers'
    return df


# @cleaner
def drop_untagged(df):
    """Drop untagged transactions."""
    mask = (df.up_tag.eq('no tag')
            & df.manual_tag.eq('no tag')
            & df.auto_tag.eq('no tag'))
    return df[~mask]


# @cleaner
def tag_corrections(df):
    """Correct or consolidate tag variable."""
    new_tags = {
        'housing': ['rent', 'mortgage or rent', 'mortgage payment']
    }
    for new_tag, old_tags in new_tags.items():
        pattern = '|'.join(old_tags)
        mask = df[df.tag_up].str.match(pattern)
        df.loc[mask, 'tag'] = new_tag
    return df


# @cleaner
def drop_card_repayments(df):
    """Drop card repayment transactions from current accounts."""
    tags = ['credit card repayment', 'credit card payment', 'credit card']
    pattern = '|'.join(tags)
    mask = df.auto_tag.str.contains(pattern) & df.account_type.eq('current')
    return df[~mask]


# @cleaner
def clean_tags(df):
    """Replace parenthesis with dash for save regex searches."""
    for tag in ['up_tag', 'auto_tag', 'manual_tag']:
        df[tag] = df[tag].str.replace('(', '- ').str.replace(')', '')
    return df


