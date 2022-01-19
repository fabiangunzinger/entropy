"""
Create dataset used for analysis.
"""

import numpy as np
import pandas as pd

import entropy.helpers.data as hd
import entropy.helpers.aws as ha


month = pd.Grouper(key="date", freq="m")
idx_cols = ["user_id", month]

column_makers = []


def column_adder(func):
    column_makers.append(func)
    return func


def trim_columns_upper(df, pct=0, ends="upper"):
    return df.apply(lambda x: hd.trim(x, pct=pct))


@column_adder
def obs_count(df):
    return df.groupby(idx_cols).id.count().rename("obs")


@column_adder
def account_balances(df):
    """Calculates average monthly balances for user's savings and current accounts."""
    return (
        df.loc[df.account_type.isin(["current", "savings"])]
        # daily account balances
        .groupby(
            ["user_id", "account_type", "account_id", "date"],
            observed=True,
        )
        .balance.first()
        # daily account type balances
        .groupby(["user_id", "account_type", "date"], observed=True)
        .sum()
        # monthly account type mean balance
        .reset_index()
        .set_index("date")
        .groupby(["user_id", "account_type"])
        .balance.resample("m")
        .mean()
        # reformat
        .unstack(level="account_type")
        .rename(columns={"current": "balance_ca", "savings": "balance_sa"})
    )


@column_adder
def savings_accounts_flows(df):
    """Calculates monthly inflows, outflows, and net-inflows into user's savings accounts.

    Also calculates scaled flows by dividing by users monthly income.
    """
    df = df.copy()
    df["debit"] = df.debit.replace({True: "sa_outflows", False: "sa_inflows"})
    is_not_interest_txn = ~df.tag_auto.str.contains("interest", na=False)
    is_savings_account = df.account_type.eq("savings")
    mask = is_not_interest_txn & is_savings_account
    group_cols = idx_cols + ["income", "debit"]

    return (
        df[mask]
        .groupby(group_cols)
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
def total_monthly_spend(df):
    """Calculates log of total spend per user-month."""
    mask = df.tag_group.eq("spend")
    return (
        df[mask]
        .groupby(idx_cols)
        .amount.sum()
        .apply(np.log)
        .rename("total_monthly_spend")
    )


@column_adder
def tag_monthly_spend(df):
    """Calculates spend per tag per user-month."""
    df = df.copy()
    df["tag"] = df.tag.cat.rename_categories(lambda x: "tag_spend_" + x)
    mask = df.tag_group.eq("spend")
    group_cols = idx_cols + ["tag"]
    df = df[mask].groupby(group_cols, observed=True).amount.sum().unstack().fillna(0)
    row_totals = df.sum(1)
    return df.div(row_totals, axis=0)


@column_adder
def constant_vars(df):
    """Add variables that are constant at the user-month level."""
    df = df.copy()
    df["age"] = df.date.dt.year - df.user_yob
    df["log_income"] = np.log(df.income)
    cols = [
        "entropy_sptac",
        "income",
        "log_income",
        "user_female",
        "age",
        "region",
    ]
    return df.groupby(idx_cols)[cols].first()


def trim_columns(df, col_names, **kwargs):
    """Returns df with trimmed values for selected columns."""
    df = df.copy()
    df[col_names] = df[col_names].apply(hd.trim, **kwargs)
    return df


def main(df):
    data = pd.concat((func(df) for func in column_makers), axis=1)

    colnames_trim_upper = hd.colname_subset(data, "sa_(?:scaled_)?(?:inflows|outflows)")
    colnames_trim_both = hd.colname_subset(data, "balance|sa_scaled|entropy|spend")
    data = trim_columns(data, colnames_trim_upper, how="upper", pct=1)
    data = trim_columns(data, colnames_trim_both, how="both", pct=1)
    return data


if __name__ == "__main__":

    SAMPLE = "XX7"
    fp_txn = f"s3://3di-project-entropy/entropy_{SAMPLE}.parquet"
    fp_analysis = f"s3://3di-project-entropy/analysis_data.parquet"
    txn_data = ha.read_parquet(fp_txn)
    analysis_data = main(txn_data)
    ha.write_parquet(analysis_data, fp_analysis, index=True)
