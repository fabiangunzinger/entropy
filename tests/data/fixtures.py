import pandas as pd
import pytest


@pytest.fixture
def mdb1():
    return pd.DataFrame(
        {
            "user_id": [1, 1, 1],
            "date": pd.to_datetime(["2020-01-11", "2020-02-12", "2020-03-13"]),
            "amount": [11.1, 22.2, 33.3],
            "desc": ["costa coffee", "waitrose", "pure gym"],
        }
    )


@pytest.fixture
def mdb_data():
    df = pd.read_parquet("~/tmp/mdb_000.parquet")
    return df
