"""
Create dataset used for analysis.

"""
import collections

import numpy as np
import pandas as pd

import entropy.helpers.aws as ha
import entropy.helpers.data as hd
import entropy.helpers.helpers as hh


month = pd.Grouper(key="date", freq="m")
idx_cols = ["user_id", month]

column_makers = []
control_variables = []


def column_adder(func):
    column_makers.append(func)
    return func


@column_adder
def txn_counts(df):
    group_cols = idx_cols + ["account_type"]
    return (
        df.groupby(group_cols, observed=True)
        .size()
        .unstack()
        .fillna(0)
        .loc[:, ["savings", "current"]]
        .rename(columns=lambda x: f"txn_count_{x[0]}a")
    )


@column_adder
def savings_accounts_flows(df):
    """Calculates monthly inflows, outflows, and net-inflows into user's savings accounts.

    Also calculates scaled flows by dividing by users monthly income.
    """
    df = df.copy()
    is_not_interest_txn = ~df.tag_auto.str.contains("interest", na=False)
    is_savings_account = df.account_type.eq("savings")
    is_savings_flow = is_not_interest_txn & is_savings_account
    df["amount"] = df.amount.where(is_savings_flow, np.nan)
    df["debit"] = df.debit.map({True: "sa_outflows", False: "sa_inflows"})
    group_cols = idx_cols + ["income", "debit"]
    return (
        df.groupby(group_cols)
        .amount.sum()
        .abs()
        .unstack()
        .fillna(0)
        .reset_index("income")
        .assign(
            sa_net_inflows=lambda df: df.sa_inflows - df.sa_outflows,
            sa_scaled_inflows=lambda df: df.sa_inflows / (df.income / 12),
            sa_scaled_outflows=lambda df: df.sa_outflows / (df.income / 12),
            sa_scaled_net_inflows=lambda df: df.sa_net_inflows / (df.income / 12),
        )
        .drop(columns="income")
    )


@column_adder
def monthly_spend(df):
    """Calculates spend and log spend per user-month."""
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)

    return df.groupby(idx_cols).amount.agg(
        monthly_spend="sum", log_monthly_spend=lambda s: np.log(s.sum())
    )


@column_adder
def tag_monthly_spend_prop(df):
    """Calculates spend per tag per user-month as proportion of total monthly spend."""
    df = df.copy()
    is_spend = df.tag_group.eq("spend") & df.debit
    df["amount"] = df.amount.where(is_spend, np.nan)
    df["tag"] = df.tag.where(is_spend, np.nan)
    df["tag"] = df.tag.cat.rename_categories(lambda x: "prop_spend_" + x)
    group_cols = idx_cols + ["tag"]
    return (
        df.groupby(group_cols, observed=True)
        .amount.sum()
        .unstack()
        .fillna(0)
        .pipe(lambda df: df.div(df.sum(1), axis=0))
    )


@column_adder
def income(df):
    """Adds income variables."""
    df = df.copy()
    df["log_income"] = np.log(df.income)
    cols = ["income", "log_income"]
    return df.groupby(idx_cols)[cols].first()


@column_adder
def demographics(df):
    """Adds demographic variable."""
    df = df.copy()
    df["age"] = df.date.dt.year - df.yob
    cols = ["female", "age", "region"]
    return df.groupby(idx_cols)[cols].first()


@column_adder
def entropy(df):
    """Adds all entropy variables."""
    cols = hd.colname_subset(df, "entropy")
    return df.groupby(idx_cols)[cols].first()


def validator(df):
    assert df.isna().sum().sum() == 0
    return df


@hh.timer
def main(txn_data=None):
    """Produces analysis data from transactions data."""
    if txn_data is None:
        SAMPLE = "XX7"
        fp_txn = f"s3://3di-project-entropy/entropy_{SAMPLE}.parquet"
        txn_data = ha.read_parquet(fp_txn)
    analysis_data = pd.concat(
        (func(txn_data) for func in column_makers), axis=1, join="outer"
    )
    fp = f"s3://3di-project-entropy/analysis_data.parquet"
    ha.write_parquet(analysis_data, fp, index=True)
    validator(analysis_data)


if __name__ == "__main__":
    main()
