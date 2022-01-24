import itertools
import re
import string
import numpy as np

import entropy.data.txn_classifications as tc


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
        "Account Created Date": "account_created",
        "Account Reference": "account_id",
        "Derived Gender": "gender",
        "LSOA": "lsoa",
        "MSOA": "msoa",
        "Merchant Name": "merchant",
        "Postcode": "postcode",
        "Provider Group Name": "account_provider",
        "Salary Range": "salary_range",
        "Transaction Date": "date",
        "Transaction Description": "desc",
        "Transaction Reference": "id",
        "Transaction Updated Flag": "updated_flag",
        "User Reference": "user_id",
        "Year of Birth": "yob",
        "Auto Purpose Tag Name": "tag_auto",
        "Manual Tag Name": "tag_manual",
        "User Precedence Tag Name": "tag_up",
        "Latest Recorded Balance": "latest_balance",
    }
    return df.rename(columns=new_names)


@cleaner
def clean_headers(df):
    """Converts column headers to snake case."""
    df.columns = (
        df.columns.str.lower().str.replace(r"[\s\.]", "_", regex=True).str.strip()
    )
    return df


@cleaner
def drop_unneeded_vars(df):
    vars = [
        "lsoa",
        "msoa",
        "salary_range",
        "data_warehouse_date_created",
        "data_warehouse_date_last_updated",
        "updated_flag",
    ]
    return df.drop(columns=vars)


@cleaner
def add_year_month_variable(df):
    """Creates year-month date as helper variable."""
    y = df.date.dt.year * 100
    m = df.date.dt.month
    df["ym"] = y + m
    return df


@cleaner
def drop_first_and_last_month(df):
    """Drops first and last month for each user.

    These months have incomplete data for users who joined and left MDB during
    the month, which would bias monthly entropy scores downwards (if we only
    observe a single txn, entropy would be 0).
    """
    g = df.groupby("user_id")
    first_month = g.ym.transform(min)
    last_month = g.ym.transform(max)
    return df[df.ym.between(first_month, last_month, inclusive="neither")]


@cleaner
def lowercase_categories(df):
    """Converts all category values to lowercase to simplify regex searches.

    Recasts categories because casting to lowercase can lead to duplicate
    categories.
    """
    cat_vars = df.select_dtypes("category").columns
    df[cat_vars] = df[cat_vars].apply(lambda x: x.str.lower()).astype("category")
    return df


@cleaner
def drop_missing_txn_desc(df):
    return df[df.desc.notna()]


@cleaner
def gender_to_female(df):
    """Replaces gender variable with female dummy.

    Uses float type becuase bool type doesn't handle na values well.
    """
    mapping = {"f": 1, "m": 0, "u": np.nan}
    df["female"] = df.gender.map(mapping).astype("float32")
    return df.drop(columns="gender")


@cleaner
def credit_debit_to_debit(df):
    """Replaces credit_debit variable with credit dummy."""
    df["debit"] = df.credit_debit.eq("debit")
    return df.drop(columns="credit_debit")


@cleaner
def sign_amount(df):
    """Makes credits negative."""
    df["amount"] = df.amount.where(df.debit, df.amount.mul(-1))
    return df


@cleaner
def missings_to_nan(df):
    """Converts missing category values to NaN."""
    mbl = "merchant_business_line"
    mbl_missing = ["no merchant business line", "unknown merchant"]
    df[mbl] = df[mbl].cat.remove_categories(mbl_missing)
    df["merchant"] = df["merchant"].cat.remove_categories(["no merchant"])
    df["tag_up"] = df["tag_up"].cat.remove_categories(["no tag"])
    df["tag_auto"] = df["tag_auto"].cat.remove_categories(["no tag"])
    df["tag_manual"] = df["tag_manual"].cat.remove_categories(["no tag"])
    return df


@cleaner
def zero_balances_to_missing(df):
    """Replaces zero latest balances with missings.

    Latest balance column refers to account balance at last account
    refresh date. Exact zero values are likely due to unsuccessful
    account refresh (see data dictionary) and thus treated as missing.
    """
    df["latest_balance"] = df.latest_balance.replace(0, np.nan)
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
        pattern = "|".join(escaped_tags)
        mask = df.tag_auto.str.fullmatch(pattern, na=False)
        df.loc[mask, col_name] = group

    return df


@cleaner
def add_tag(df):
    """Creates custom transaction tags for spends, income, and transfers."""
    df["tag"] = np.nan
    _apply_grouping(tc.spend_subgroups, df, "tag")
    _apply_grouping(tc.income_subgroups, df, "tag")
    _apply_grouping(tc.transfers_subgroups, df, "tag")
    df["tag"] = df.tag.astype("category")
    return df


@cleaner
def tag_corrections(df):
    """Fix issues with automatic tagging.

    Correction is applied to `tag` to leave `tag_auto`
    unchanged but to ensure that correction will be taken
    into account in `add_tag_group()` below.
    """
    # tag untagged as transfer if desc clearly indicates as much
    tfr_strings = [" ft", " trf", "xfer", "transfer"]
    tfr_pattern = "|".join(tfr_strings)
    exclude_strings = ["fee", "interest", "rewards"]
    exclude_pattern = "|".join(exclude_strings)
    mask = (
        df.desc.str.contains(tfr_pattern)
        & df.desc.str.contains(exclude_pattern).eq(False)
        & df.tag.isna()
    )
    df.loc[mask, "tag"] = "other_transfers"

    # tag untagged as other_spend if desc contains "bbp",
    # which is short for bill payment
    mask = df.desc.str.contains("bbp") & df.tag.isna()
    df.loc[mask, "tag"] = "other_spend"

    # reclassify 'interest income' as finance spend if txn is a debit
    # these are mostly overdraft fees
    mask = df.tag_auto.eq("interest income") & df.debit
    df.loc[mask, "tag"] = "finance"

    return df


@cleaner
def add_tag_group(df):
    """Groups transactions into income, spend, and transfers."""
    df["tag_group"] = np.nan
    _apply_grouping(tc.tag_groups, df, "tag_group")
    df["tag_group"] = df.tag_group.astype("category")
    return df


@cleaner
def clean_description(df):
    """Cleans up txnd description for better duplicate detection.

    Removes common suffixes such as -vis, -p/p, and - e gbp; all
    punctuation; multiple x characters, which are used to mask card
    or account numbers; and extra whitespace. Also splits digits
    suffixes -- but not prefixes, as these are usually dates -- from
    sequences of two or more letters (e.g. 'no14' becomes 'no 14',
    'o2', and '14jan' remain unchanged).
    """
    kwargs = dict(repl=" ", regex=True)
    df["desco"] = df.desc
    df["desc"] = (
        df.desc.str.replace(r"-\s(\w\s)?.{2,3}$", **kwargs)
        .str.replace(fr"[{string.punctuation}]", **kwargs)
        .str.replace(r"[x]{2,}", **kwargs)
        .str.replace(r"(?<=[a-zA-Z]{2})(?=\d)", **kwargs)
        .str.replace(r"\s{2,}", **kwargs)
        .str.strip()
    )
    df["desc"] = df.desc.astype("category")
    return df


@cleaner
def drop_type1_dups(df):
    """Drops Type 1 duplicates.

    A Type 1 duplicate is the second of two txns with identical user and
    account ids, dates, amounts, and txn descriptions.
    """
    df = df.copy()
    cols = ["user_id", "account_id", "date", "amount", "desc"]
    return df.drop_duplicates(subset=cols)


def _potential_type2_dups(df):
    """Returns desc and duplicate group id for potential Type 2 duplicates."""
    cols = ["date", "user_id", "account_id", "amount"]
    mask = df.duplicated(subset=cols, keep=False)
    assign_group_id = lambda df: df.groupby(cols).ngroup()
    return df.loc[mask].assign(group=assign_group_id).loc[:, ["desc", "group"]]


def _each_word_in_string(words, string):
    """Tests whether each word from words appears in string.
    Allows each substring in string to be matched only once.
    """
    unmatched = string
    for w in words:
        if w not in unmatched:
            return False
        unmatched = unmatched.replace(w, "", 1)
    return True


def _type2_dups_indices(g):
    """Checks for each txn pair in a group whether one txn is a Type 2
    duplicate of the other, and returns idx of all duplicates in group.
    """
    dups = []
    pairs = list(itertools.combinations(g.index, 2))
    for first, second in pairs:
        words = g.loc[first].desc.split()
        string = g.loc[second].desc
        if _each_word_in_string(words, string):
            dups.append(first)
            break
        words = g.loc[second].desc.split()
        string = g.loc[first].desc
        if _each_word_in_string(words, string):
            dups.append(second)
    return dups


@cleaner
def drop_type2_dups(df):
    """Drops Type 2 duplicates.

    A Type 2 duplicate is a txn whose user id, account id, date, and amount
    are identical to another txn, and whose txn description is similar to that
    other txn, where "similar" means that each word in the txn description
    appears in the description of the other txn.
    """
    potential_dups = _potential_type2_dups(df)
    g = potential_dups.groupby("group")
    group_dup_indices = g.apply(_type2_dups_indices)
    dup_indices = group_dup_indices.sum()
    return df.drop(dup_indices)


@cleaner
def order_and_sort(df):
    """Orders columns and sort values."""
    cols = df.columns
    first = ["id", "date", "user_id", "amount", "desc", "merchant", "tag_group", "tag"]
    user = cols[cols.str.startswith("user") & ~cols.isin(first)]
    account = cols[cols.str.startswith("account") & ~cols.isin(first)]
    txn = cols[~cols.isin(user.append(account)) & ~cols.isin(first)]
    order = first + sorted(user) + sorted(account) + sorted(txn)

    return df[order].sort_values(["user_id", "date"])
