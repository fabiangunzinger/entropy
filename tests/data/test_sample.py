import pandas as pd
import pytest

from ..entropy.data import cleaners

def test_drop_last_month_passes(df):
    data = cleaners.drop_last_month(df)
    assert data.date.dt.month.max() == 2




def test_df(mdb_data):
    assert len(mdb_data.columns) == 27




