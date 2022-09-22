"""
Functions to create columns for analysis dataset at user-month frequency.

"""

import re
import os
import functools

import numpy as np
import pandas as pd
from scipy import stats
import s3fs

from src import config
import src.helpers.data as hd
import src.helpers.helpers as hh


TIMER_ON = False


aggregators = []


def aggregator(func):
    aggregators.append(func)
    return func


@aggregator
@hh.timer(on=TIMER_ON)
def numeric_ym(df):
    """Numeric ym variable for use in R."""
    group_cols = [df.user_id, df.ym]
    g = df.ym.groupby(group_cols).first()
    yr = g.dt.year.astype("string")
    mt = g.dt.month.astype("string").apply("{:0>2}".format)
    return (yr + mt).astype("int").rename("ymn")


@aggregator
@hh.timer(on=TIMER_ON)
def month(df):
    """Numeric month for use as FE."""
    group_cols = [df.user_id, df.ym]
    return df.date.dt.month.groupby(group_cols).first().rename("month")


@aggregator
@hh.timer(on=TIMER_ON)
def txns_count(df):
    group_cols = [df.user_id, df.ym]
    return df.groupby(group_cols).id.size().rename("txns_count")


@aggregator
@hh.timer(on=TIMER_ON)
def txns_volume(df):
    group_cols = [df.user_id, df.ym]
    return df.amount.abs().groupby(group_cols).sum().rename("txns_volume")


@aggregator
@hh.timer
def spend_txns_count(df):
    is_spend = df.tag_group.eq("spend") & df.is_debit
    group_cols = [df.user_id, df.ym]
    return is_spend.groupby(group_cols).sum().rename("txns_count_spend")


@aggregator
@hh.timer
def txns_counts_by_account_type(df):
    group_cols = [df.user_id, df.ym, df.account_type]
    return (
        df.groupby(group_cols, observed=True)
        .size()
        .unstack()
        .fillna(0)
        .loc[:, ["savings", "current"]]
        .rename(columns=lambda x: f"txns_count_{x[0]}a")
    )


@aggregator
@hh.timer
def benefits(df):
    """Dummy indicating (non-family) benefit receipt."""
    tags = ["benefits", "job seekers benefits", "other benefits", "incapacity benefits"]
    is_benefit = df.tag_auto.isin(tags)
    benefits = df.amount.where(is_benefit, 0)
    group_cols = [df.user_id, df.ym]
    return benefits.groupby(group_cols).sum().lt(0).astype(int).rename("has_benefits")


@aggregator
@hh.timer
def overdraft_fees(df):
    """Dummy for whether overdraft fees were paid."""
    pattern = r"(?:od|o/d|overdraft).*(?:fee|interest)"
    is_od_fee = df.desc.str.contains(pattern) & df.is_debit
    od_fees = df.id.where(is_od_fee, np.nan)
    group_cols = [df.user_id, df.ym]
    return od_fees.groupby(group_cols).count().gt(0).astype(int).rename("has_od_fees")


@aggregator
@hh.timer(on=TIMER_ON)
def income(df):
    """Month and year income in '000s for easier coefficient comparison."""
    is_income_pmt = df.tag_group.eq("income") & ~df.is_debit
    inc_pmts = df.amount.where(is_income_pmt, 0).mul(-1).div(1000)
    year = df.date.dt.year.rename("year")

    month_income = (
        inc_pmts.groupby([df.user_id, df.ym, year]).sum().rename("month_income")
    )

    year_income = inc_pmts.groupby([df.user_id, year]).sum().rename("year_income")

    month_income_mean = (
        inc_pmts.groupby([df.user_id, df.ym, year])
        .sum()
        .groupby(["user_id", "year"])
        .transform("mean")
        .rename("month_income_mean")
    )

    income_variability = (
        month_income.groupby("user_id")
        .rolling(window=12, min_periods=1)
        .std()
        .droplevel(0)
        .rename("income_var")
    )

    has_mt_income = month_income.gt(0).astype(int).rename("has_month_income")

    idx_merge = functools.partial(pd.merge, left_index=True, right_index=True)

    return (
        month_income.pipe(idx_merge, year_income)
        .pipe(idx_merge, month_income_mean)
        .pipe(idx_merge, income_variability)
        .pipe(idx_merge, has_mt_income)
    ).droplevel("year")


@aggregator
@hh.timer(on=TIMER_ON)
def savings_accounts_flows(df):
    """Saving accounts flows variables."""
    is_sa_flow = df.account_type.eq("savings") & df.amount.abs().gt(5)
    sa_flows = df.amount.where(df.is_sa_flow, 0)
    in_out = df.is_debit.map({True: "outflows", False: "inflows"})
    month_income = income(df).month_income
    group_vars = [df.user_id, df.ym, in_out]
    return (
        sa_flows.groupby(group_vars)
        .sum()
        .abs()
        .unstack()
        .fillna(0)
        .assign(
            netflows=lambda df: df.inflows - df.outflows,
            netflows_norm=lambda df: df.netflows / month_income,
            inflows_norm=lambda df: df.inflows / month_income,
            outflows_norm=lambda df: df.outflows / month_income,
            has_pos_netflows=lambda df: (df.netflows > 0).astype(int),
            pos_netflows=lambda df: df.netflows * df.has_pos_netflows,
            has_inflows=lambda df: (df.inflows > 0).astype(int),
        )
        .replace([np.inf, -np.inf, np.nan], 0)
    )


@aggregator
@hh.timer(on=TIMER_ON)
def user_registration_ym(df):
    """Year-month of user registration."""
    group_cols = [df.user_id, df.ym]
    return (
        df.groupby(group_cols)
        .user_registration_date.first()
        .dt.to_period("m")
        .rename("user_reg_ym")
    )


@aggregator
@hh.timer(on=TIMER_ON)
def month_spend(df):
    """Total monthly spend in '000s of pounds for simpler coefficient comparison."""
    is_spend = df.tag_group.eq("spend") & df.is_debit
    spend = df.amount.where(is_spend, np.nan).div(1000)
    group_cols = [df.user_id, df.ym]
    return spend.groupby(group_cols).sum().rename("month_spend")


@aggregator
@hh.timer(on=TIMER_ON)
def age(df):
    """Adds user age at time of signup."""
    group_cols = [df.user_id, df.ym]
    age = df.user_registration_date.dt.year - df.birth_year
    return age.groupby(group_cols).first().rename("age")


@aggregator
@hh.timer(on=TIMER_ON)
def female(df):
    """Dummy for whether user is a women."""
    group_cols = [df.user_id, df.ym]
    return df.groupby(group_cols).is_female.first()


@aggregator
@hh.timer(on=TIMER_ON)
def region(df):
    """Region and urban dummy."""
    group_cols = [df.user_id, df.ym]
    return (
        df.rename(columns={"region_name": "region"})
        .groupby(group_cols)[["region", "is_urban"]]
        .first()
        .assign(region_code=lambda df: df.region.factorize()[0])
    )


@aggregator
@hh.timer(on=TIMER_ON)
def has_savings_account(df):
    """Indicator for whether user has at least one savings account added.

    We can only observe an account as added when we observe a transaction. So
    the indicator is one when we observe at least one sa txn for the user.
    """
    group_cols = [df.user_id, df.ym]
    return (
        df.account_type.eq("savings")
        .groupby(group_cols)
        .max()
        .groupby("user_id")
        .transform("max")
        .rename("has_savings_account")
    )


@aggregator
@hh.timer(on=TIMER_ON)
def has_current_account(df):
    """Indicator for whether user has at least one current account added.

    We can only observe an account as added when we observe a transaction. So
    the indicator is one when we observe at least one current account txn for
    the user.
    """
    group_cols = [df.user_id, df.ym]
    return (
        df.account_type.eq("current")
        .groupby(group_cols)
        .max()
        .groupby("user_id")
        .transform("max")
        .rename("has_current_account")
    )


@aggregator
@hh.timer(on=TIMER_ON)
def generation(df):
    """Generation of user.

    Source: https://www.beresfordresearch.com/age-range-by-generation/
    """

    def gen(x):
        if np.isnan(x):
            gen = np.nan
        elif 1928 <= x <= 1945:
            gen = "Post War"
        elif 1946 <= x <= 1964:
            gen = "Boomers"
        elif 1965 <= x <= 1980:
            gen = "Gen X"
        elif 1981 <= x <= 1996:
            gen = "Millennials"
        else:
            gen = "Gen Z"
        return gen

    group_cols = [df.user_id, df.ym]
    gens = ["Post War", "Boomers", "Gen X", "Millennials", "Gen Z"]
    gen_cats = pd.CategoricalDtype(gens, ordered=True)
    return (
        df.groupby(group_cols)
        .birth_year.first()
        .map(gen)
        .astype(gen_cats)
        .rename("generation")
        .to_frame()
        .assign(generation_code=lambda df: df.generation.cat.codes)
    )


@aggregator
@hh.timer(on=TIMER_ON)
def proportion_credit(df):
    """Proportion of month spend paid by credit card."""
    group_cols = [df.user_id, df.ym]
    is_spend = df.tag_group.eq("spend") & df.is_debit
    spend = df.amount.where(is_spend, np.nan).groupby(group_cols).sum()
    is_cc_spend = is_spend & df.account_type.eq("credit card")
    cc_spend = df.amount.where(is_cc_spend, np.nan).groupby(group_cols).sum()
    return cc_spend.div(spend).rename("prop_credit")


@aggregator
@hh.timer(on=TIMER_ON)
def num_accounts(df):
    """Number of active accounts."""
    group_cols = [df.user_id, df.ym]
    total = (
        df.groupby("user_id")
        .account_id.nunique()
        .rename("accounts_total")
        .reset_index()
    )
    return (
        df.groupby(group_cols)
        .account_id.nunique()
        .rename("accounts_active")
        .reset_index()
        .merge(total)
        .set_index(["user_id", "ym"])
    )


@aggregator
@hh.timer(on=TIMER_ON)
def investments(df):
    """Flows into investment and pension funds."""
    group_cols = [df.user_id, df.ym]
    invest_tags = [
        "pension or investments",
        "investment - other",
        "investments or shares",
    ]
    is_invest = df.tag_auto.isin(invest_tags) & df.is_debit
    invest = df.amount.where(is_invest, 0)
    return invest.groupby(group_cols).sum().rename("investments")


@aggregator
@hh.timer(on=TIMER_ON)
def user_precedence_tag_based_savings(df):
    """
    Transfers from current accounts to (linked and unlinked)
    savings accounts based on manual user tags.
    """
    group_vars = [df.user_id, df.ym]
    is_tfr = (
        df.tag_up.str.contains("saving") & df.account_type.eq("current") & df.is_debit
    )
    tfr = df.amount.where(is_tfr, 0)
    return tfr.groupby(group_vars).sum().rename("up_savings")


@aggregator
@hh.timer(on=TIMER_ON)
def current_account_transfers(df):
    """
    Transfers from current accounts.
    """
    group_vars = [df.user_id, df.ym]
    is_tfr = df.tag_group.eq("transfers") & df.account_type.eq("current") & df.is_debit
    tfr = df.amount.where(is_tfr, 0)
    return tfr.groupby(group_vars).sum().rename("ca_transfers")


@aggregator
@hh.timer(on=TIMER_ON)
def credit_card_payments(df):
    """
    Payments into credit card accounts.
    """
    group_vars = [df.user_id, df.ym]
    is_cc_inflow = (
        df.account_type.eq("credit card")
        & ~df.is_debit
        & df.tag_auto.eq("credit card")  # discards refunds
    )
    cc_inflow = df.amount.where(is_cc_inflow, 0).mul(-1)
    return cc_inflow.groupby(group_vars).sum().rename("cc_payments")


@aggregator
@hh.timer(on=TIMER_ON)
def loan_funds(df):
    """Loan funds inflow."""
    LOAN_FUND_TAGS = [
        "personal loan",
        "unsecured loan funds",
        "payday loan",
        "payday loan funds",
        "student loan funds",
    ]
    group_vars = [df.user_id, df.ym]
    is_loan_fund = df.tag_auto.isin(LOAN_FUND_TAGS) & ~df.is_debit
    loan_fund = df.amount.where(is_loan_fund, 0).mul(-1)
    return loan_fund.groupby(group_vars).sum().rename("loan_funds")


@aggregator
@hh.timer(on=TIMER_ON)
def loan_repayments(df):
    """Loan repayments."""
    LOAN_RPMT_TAGS = [
        "secured loan repayment",
        "unsecured loan repayment",
        "student loan repayment",
        "payday loan",
        "personal loan",
    ]
    group_vars = [df.user_id, df.ym]
    is_loan_rpmt = df.tag_auto.isin(LOAN_RPMT_TAGS) & df.is_debit
    loan_rpmts = df.amount.where(is_loan_rpmt, 0)
    return loan_rpmts.groupby(group_vars).sum().rename("loan_rpmts")


@aggregator
@hh.timer
def category_nunique(df):
    """Number of unique categories spent on per user-month."""
    is_spend = df.tag_group.eq("spend") & df.is_debit
    cat_vars = ["tag", "tag_spend", "merchant"]
    group_cols = [df.user_id, df.ym]
    return (
        df[cat_vars]
        .where(is_spend, np.nan)
        .groupby(group_cols)
        .nunique()
        .rename(columns=lambda x: "nunique_" + x)
    )


DSPEND_GROUPS = {
    "other": [
        "beauty products",
        "beauty treatments",
        "appearance",
        "accessories",
        "jewellery",
        "personal electronics",
        "hotel/b&b",
        "gambling",
        "games and gaming",
        "enjoyment",
    ],
    "clothes": [
        "clothes",
        "clothes - designer or other",
        "clothes - everyday or work",
        "clothes - other",
        "designer clothes",
        "shoes",
    ],
    "groceries": [
        "food, groceries, household",
        "groceries",
        "supermarket",
    ],
    "entertainment": [
        "cinema",
        "concert & theatre",
        "entertainment, tv, media",
        "sports event",
    ],
    "food": [
        "dining and drinking",
        "dining or going out",
        "lunch or snacks",
        "take-away",
    ],
}


@aggregator
@hh.timer(on=TIMER_ON)
def dspend(df):
    """Discretionary spend."""
    group_cols = [df.user_id, df.ym]
    dspend_tags = [tag for group, tags in DSPEND_GROUPS.items() for tag in tags]
    is_dspend = df.tag_auto.isin(dspend_tags) & df.is_debit
    dspend = df.amount.where(is_dspend, np.nan)
    return dspend.groupby(group_cols).agg(
        [("dspend", "sum"), ("dspend_count", "count"), ("dspend_mean", "mean")]
    )


@aggregator
@hh.timer(on=TIMER_ON)
def dspend_groups(df):
    """Spends on discretionary spend groups."""
    # Classify dspends
    df["dspend"] = np.nan
    for group, tags in DSPEND_GROUPS.items():
        mask = df.tag_auto.isin(tags) & df.is_debit
        df.loc[mask, "dspend"] = "_".join(["dspend", group])

    group_cols = [df.user_id, df.ym, df.dspend]
    is_dspend = df.dspend.notna()
    dspend = df.amount.where(is_dspend, np.nan)
    return dspend.groupby(group_cols).sum().unstack().fillna(0)


@aggregator
@hh.timer(on=TIMER_ON)
def dspend_direct_debit(df):
    """Discretionary spend paid by debit direct."""
    group_cols = [df.user_id, df.ym]
    dd_pattern = "direct debit|dd$|d/d$|ddr$"
    dspend_tags = [tag for group, tags in DSPEND_GROUPS.items() for tag in tags]
    is_dd_dspend = (
        df.desc.str.contains(dd_pattern) & df.tag_auto.isin(dspend_tags) & df.is_debit
    )
    dd_dspend = df.amount.where(is_dd_dspend, np.nan)
    return dd_dspend.groupby(group_cols).sum().rename("dspend_dd")


@aggregator
@hh.timer
def month_spend_txn_value_and_counts(df):
    """Monthly value and count of spend txns per category.

    Spend value expressed in £'000s to ease coefficient comparison.
    """

    def colname(x):
        """Turn x into proper column name."""
        pattern = "\.|,| |\(|\)|&"
        name = re.sub(pattern, "_", x)
        return re.sub("_+", "_", name)

    def spend_in_1000s(s):
        return s.sum() / 1000

    is_spend = df.tag_group.eq("spend") & df.is_debit
    spend_amount = df.amount.where(is_spend, np.nan)
    cat_vars = ["tag", "tag_spend", "merchant"]
    frames = []

    for cat in cat_vars:
        spend_cats = df[cat].where(is_spend, np.nan)
        group_cols = [df.user_id, df.ym, spend_cats]
        data = (
            spend_amount.groupby(group_cols, observed=True)
            .agg([(f"sp_{cat}", spend_in_1000s), (f"ct_{cat}", "count")])
            .unstack()
            .pipe(lambda df: df.set_axis(df.columns.map("_".join), axis=1))
            .fillna(0)
        )
        frames.append(data)

    return pd.concat(frames, axis=1)


def _entropy_base_values(df, cat, stat="size", wknd=False):
    """Spend txns counts or values for each cat by user-month.

    Args:
    df: A txn-level dataframe.
    cat: A column from df to be used for categorising spending transactions.
    stat: A stat in {'size', 'sum'} to calculate entropy based on counts or
      volume, respectively.
    wknd: A Boolean indicating whether spend txns should be categorised
      by (cat, wknd), if True, or by (cat), if False, where wknd is a dummy
      indicating whether a txn is dated as a Sa, So, or Mo.

    Returns:
      A DataFrame with user-month rows, category columns, and count values.
    """
    is_cat_observed_spend = df.tag_group.eq("spend") & df.is_debit & df[cat].notna()
    df = df.loc[is_cat_observed_spend].copy()
    if wknd:
        is_wknd = df.date.dt.dayofweek.isin([5, 6, 0]).astype(str)
        df[cat] = df[cat].astype(str) + is_wknd
    group_cols = [df.user_id, df.ym] + [cat]
    return df.groupby(group_cols, observed=True).amount.agg(stat).unstack().fillna(0)


def _entropy_scores(df, norm=False, zscore=False, smooth=False):
    """Returns row-wise Shannon entropy scores based on base values.

    Args:
    df: A DataFrame with entity rows, category columns, and count values.
    norm: A Boolean value indicating whether to divide entorpy by
      max entropy.
    smoothed: A Boolean value indicating whether to apply additive smoothing
      to the base values in df before calculating probabilities.

    Returns:
      A series with entropy scores for each row.
    """
    row_totals = df.sum(1)
    num_unique = len(df.columns)
    if smooth:
        probs = (df + 1).div(row_totals + num_unique, axis=0)
    else:
        probs = df.div(row_totals, axis=0)
    e = stats.entropy(probs, base=2, axis=1)
    if norm:
        e = e / np.log2(num_unique)
    if zscore:
        e = (e - e.mean()) / e.std()
    return pd.Series(e, index=df.index)


def _cat_count_std(base_values):
    """Returns row-wise standard deviation of base_values."""
    return base_values.std(1)


@aggregator
@hh.timer
def cat_based_entropy(df):
    """Calculate entropy based on category txn base values."""
    cats = ["tag", "tag_spend", "merchant"]
    scores = []
    for cat in cats:
        base_values = _entropy_base_values(df, cat, stat="size")
        scores.extend(
            [
                _entropy_scores(base_values, smooth=False).rename(f"entropy_{cat}"),
                _entropy_scores(base_values, smooth=False, zscore=True).rename(
                    f"entropy_{cat}_z"
                ),
                _entropy_scores(base_values, smooth=True).rename(f"entropy_{cat}_s"),
                _entropy_scores(base_values, smooth=True, zscore=True).rename(
                    f"entropy_{cat}_sz"
                ),
                _cat_count_std(base_values).rename(f"std_{cat}"),
            ]
        )
    return pd.concat(scores, axis=1)


@aggregator
@hh.timer
def grocery_shop_entropy(df):
    """Returns Shannon entropy based on grocery merchant counts."""

    def is_grocery_shop(df):
        """Return True if a txn is a grocery shop.

        Regex requires optional supermarket suffix because for some merchants
        (e.g. Tesco), other suffixes like 'finance' or 'fuel' also occurr,
        while those that only sell groceries (e.g. Ocado) appear without a
        suffix.
        """
        grocers = [
            "tesco",
            "sainsburys",
            "asda",
            "morrisons",
            "aldi",
            "co-op",
            "lidl",
            "waitrose",
            "iceland",
            "ocado",
        ]
        p = fr"^({'|'.join(grocers)})(:?\ssupermarket)?$"
        return df.merchant_business_line.str.match(p)

    data = df[["user_id", "ym", "tag_group", "is_debit", "amount", "date"]].copy()
    data["merchant"] = df.merchant.where(is_grocery_shop(df), np.nan)
    counts = _entropy_base_values(data, cat="merchant", stat="size", wknd=True)
    return pd.concat(
        [
            _entropy_scores(counts).rename("entropy_groc"),
            _entropy_scores(counts, zscore=True).rename("entropy_groc_z"),
            _entropy_scores(counts, smooth=True).rename("entropy_groc_s"),
            _entropy_scores(counts, smooth=True, zscore=True).rename("entropy_groc_sz"),
        ],
        axis=1,
    )
