"""
Functions to transform variables.

"""

import src.config as config
import src.helpers.data as hd


transformers = []


def transformer(func):
    """Add func to list of transformer functions."""
    transformers.append(func)
    return func


@transformer
def winsorise_upper(df):
    cols = [
        "inflows",
        "outflows",
        "pos_netflows",
        "inflows_norm",
        "outflows_norm",
        "txns_count",
        "txns_volume",
        "month_spend",
        "month_income",
        "dspend",
        "dspend_mean",
        "dspend_count",
        "dspend_clothes",
        "dspend_entertainment",
        "dspend_food",
        "dspend_groceries",
        "dspend_other",
        "dspend_dd",
        "investments",
        "up_savings",
        "ca_transfers",
        "cc_payments",
        "loan_funds",
        "loan_rpmts",
    ]
    df[cols] = df[cols].apply(hd.winsorise, pct=config.WIN_PCT, how="upper")
    return df


@transformer
def winsorise_both(df):
    cols = [
        "netflows",
        "netflows_norm",
    ]
    df[cols] = df[cols].apply(hd.winsorise, pct=config.WIN_PCT / 2, how="both")
    return df
