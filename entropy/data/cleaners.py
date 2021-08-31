import numpy as np
import pandas as pd
from mlbt import config
from .decorators import cleaner


@cleaner
def add_variables(df):
    """Create helper variables."""
    y = df.transaction_date.dt.year * 100
    m = df.transaction_date.dt.month
    df['ym'] = y + m
    return df


# @cleaner
# def drop_last_month(df):
#     """Drop last month, which might have missing data.
#     For first month, Jan 2012, we have complete data.
#     """
#     ym = df.transaction_date.dt.to_period('M')
#     return df[ym < ym.max()]


# @cleaner
# def clean_gender(df):
#     """Categorise 'u' as missing."""
#     df['gender'] = df.gender.str.replace('u', '')
#     return df


# @cleaner
# def clean_tags(df):
#     """Replace parenthesis with dash for save regex searches."""
#     for tag in ['up_tag', 'auto_tag', 'manual_tag']:
#         df[tag] = df[tag].str.replace('(', '- ').str.replace(')', '')
#     return df


# def drop_duplicate_accounts(df):
#     pass


# def drop_business_accounts(df):
#     pass


# @cleaner
# def correct_up_tag(df):
#     """Set up_tag equal to manual_tag if it exists and auto_tag otherwise.
#     This is how up_tag is supposed to behave but doesn't always.
#     """
#     manual_tag_exists = df.manual_tag.values != 'no tag'
#     df['up_tag'] = np.where(manual_tag_exists, df.manual_tag, df.auto_tag)
#     return df


# @cleaner
# def add_tag(df):
#     """Create empty corrected tag variable."""
#     df['tag'] = None
#     return df


# @cleaner
# def tag_pmt_pairs(df, knn=5):
#     """Tag payments from one account to another as transfers.

#     Identification criteria:
#     1. same user
#     2. larger than GBP50
#     3. same amount
#     4. no more than 4 days apart
#     5. of the opposite sign (debit/credit)
#     6. not already part of another transfer pair. This can happen in two ways:
#        - A txn forms a pair with two neighbours at different distances,
#          addressed in <1>.
#        - A txn forms a pair with a neighbour and the neighbour with one
#          of its own neighbours, addressed in <2>.

#     Code sorts data by user, amount, and transaction date, and checks for each
#     txn and each of its k nearest preceeding neighbours whether, together, they
#     meet the above criteria.
#     """
#     df['amount'] = df.amount.abs()
#     df = df.sort_values(['user_id', 'amount', 'transaction_date'])
#     for k in range(1, knn+1):
#         meets_conds = (
#             (df.user_id.values == df.user_id.shift(k).values)
#             & (df.amount.values > 50)
#             & (df.amount.values == df.amount.shift(k).values)
#             & (df.transaction_date.diff(k).dt.days.values <= 4)
#             & (df.credit_debit.values != df.credit_debit.shift(k).values)
#             & (df.tag.values != 'transfers')                       # <1>
#             & (df.tag.shift(k).values != 'transfers')              # <1>
#         )
#         # tag first txn of pair
#         neighbr_meets_cond = np.roll(meets_conds, k)
#         neighbr_meets_cond[:k] = False
#         is_tfr = meets_conds & ~neighbr_meets_cond                 # <2>
#         df['tag'] = np.where(is_tfr, 'transfers', df.tag)
#         # tag second txn of pair
#         mask = np.roll(meets_conds, -k)
#         mask[-k:] = False
#         df['tag'] = np.where(mask, 'transfers', df.tag)
#     return df


# @cleaner
# def tag_transfers(df):
#     """Tag txns with description indicating tranfser payment."""
#     tfr_strings = [' ft', ' trf', 'xfer', 'transfer']
#     exclude = ['fee', 'interest']
#     mask = (df.transaction_description.str.contains('|'.join(tfr_strings))
#             & ~df.transaction_description.str.contains('|'.join(exclude)))
#     df.loc[mask, 'tag'] = 'transfers'
#     return df


# @cleaner
# def drop_untagged(df):
#     """Drop untagged transactions."""
#     mask = (df.up_tag.eq('no tag')
#             & df.manual_tag.eq('no tag')
#             & df.auto_tag.eq('no tag'))
#     return df[~mask]


# @cleaner
# def tag_incomes(df):
#     """Tag earnings, pensions, benefits, and other income.
#     Based on Appendix A in Haciouglu et al. (2020).
#     """
#     incomes = {
#         'earnings': [
#             'salary or wages - main',
#             'salary or wages - other',
#             'salary - secondary',
#         ],
#         'pensions': [
#             'pension - other',
#             'pension',
#             'work pension',
#             'state pension',
#             'pension or investments',
#         ],
#         'benefits': [
#             'benefits',
#             'family benefits',
#             'job seekers benefits',
#             'other benefits',
#             'incapacity benefits'
#         ],
#         'other': [
#             'rental income - whole property',
#             'rental income - room',
#             'rental income',
#             'irregular income or gifts',
#             'miscellaneous income - other',
#             'investment income - other',
#             'loan or credit income',
#             'bond income',
#             'interest income',
#             'dividend',
#             'student loan funds',
#         ],
#     }
#     for type, tags in incomes.items():
#         tagvar = config.TAGVAR
#         pattern = '|'.join(tags)
#         mask = df[tagvar].str.match(pattern) & df.credit_debit.eq('credit')
#         df.loc[mask, 'tag'] = type + '_income'
#     return df


# @cleaner
# def tag_corrections(df):
#     """Correct or consolidate tag variable."""
#     new_tags = {
#         'housing': ['rent', 'mortgage or rent', 'mortgage payment']
#     }
#     for new_tag, old_tags in new_tags.items():
#         pattern = '|'.join(old_tags)
#         mask = df[config.TAGVAR].str.match(pattern)
#         df.loc[mask, 'tag'] = new_tag
#     return df


# @cleaner
# def fill_tag(df):
#     """Replace tag with up_tag if missing ."""
#     df['tag'] = np.where(df.tag.isna(), df.up_tag, df.tag)
#     return df


# @cleaner
# def drop_card_repayments(df):
#     """Drop card repayment transactions from current accounts."""
#     tags = ['credit card repayment', 'credit card payment', 'credit card']
#     pattern = '|'.join(tags)
#     mask = df.auto_tag.str.contains(pattern) & df.account_type.eq('current')
#     return df[~mask]


# @cleaner
# def sign_amount(df):
#     """Make credits negative."""
#     credit = df.credit_debit.values == 'credit'
#     df['amount'] = np.where(credit, df.amount.mul(-1), df.amount)
#     return df


# @cleaner
# def str_to_cat(df):
#     """Convert string columns to categoricals for efficient storage."""
#     strs = df.select_dtypes('object')
#     df[strs.columns] = strs.astype('category')
#     return df


# @cleaner
# def order_salaries(df):
#     """Turn salary range into ordered variable."""
#     cats = ['< 10k', '10k to 20k', '20k to 30k',
#             '30k to 40k', '40k to 50k', '50k to 60k',
#             '60k to 70k', '70k to 80k', '> 80k']
#     df['salary_range'] = (df.salary_range.cat
#                           .set_categories(cats, ordered=True))
#     return df


# @cleaner
# def drop_unneeded_vars(df):
#     """Drop unneeded variables."""
#     # vars = ['auto_tag', 'manual_tag', 'up_tag']
#     vars = ['auto_tag', 'manual_tag']

#     return df.drop(columns=vars)


# @cleaner
# def order_columns(df):
#     first = [
#         'user_id', 'transaction_date', 'amount',
#         'transaction_description', 'merchant_name', 'tag',
#     ]
#     rest = set(df.columns) - set(first)
#     ordered = first + list(rest)
#     return df[ordered]


# @cleaner
# def sort_rows(df):
#     return df.sort_values(['user_id', 'transaction_date'], ignore_index=True)
