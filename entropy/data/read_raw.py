import pandas as pd


def read(path):
    dtypes = {
        'Transaction Reference': 'int32',
        'User Reference': 'int32',
        'Year of Birth': 'float32',
        'Account Reference': 'int32',
        'Latest Balance': 'float32',
        'Amount': 'float32',
    }
    dates = [
        'User Registration Date',
        'Transaction Date',
        'Account Created Date',
        'Account Last Refreshed',
    ]
    strings = [
        'Salary Range', 'Postcode', 'Derived Gender',
        'Provider Group Name', 'Account Type', 'Transaction Description',
        'Credit Debit', 'User Precedence Tag Name', 'Manual Tag Name',
        'Auto Purpose Tag Name', 'Merchant Name', 'Merchant Business Line',
    ]
    str_cleaner = dict.fromkeys(strings, lambda x: x.lower().strip())

    def col_selector(col_name):
        ignore = [
            'LSOA', 'MSOA', 'Data Warehouse Date Last Updated',
            'Transaction Updated Flag', 'Data Warehouse Date Created'
        ]
        return col_name not in ignore

    return pd.read_csv(path, sep='|', parse_dates=dates,
                       usecols=col_selector, dtype=dtypes,
                       converters=str_cleaner)


def clean_names(df):
    df.columns = (df.columns
                  .str.lower()
                  .str.replace(' ', '_')
                  .str.replace('.', '_')
                  .str.strip())
    return df


def rename(df):
    new_names = {
        "user_reference": "user_id",
        "transaction_reference": "transaction_id",
        "account_reference": "account_id",
        "provider_group_name": "bank",
        "account_created_date": "account_created",
        "latest_recorded_balance": "latest_balance",
        "manual_tag_name": "manual_tag",
        "auto_purpose_tag_name": "auto_tag",
        "user_precedence_tag_name": "up_tag",
        "derived_gender": "gender",
    }
    return df.rename(columns=new_names)


def read_raw(path):
    return (
        read(path)
        .pipe(clean_names)
        .pipe(rename)
    )
