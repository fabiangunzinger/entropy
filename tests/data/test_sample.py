import pandas as pd
import pytest

@pytest.fixture
def mdb_data():
    df = pd.read_parquet('~/tmp/mdb_000.parquet')
    return df


def test_df(mdb_data):
    assert len(mdb_data.columns) == 27

