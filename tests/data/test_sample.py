import pandas as pd
import pytest

from entropy.data import cleaners
import fixtures


def test_drop_last_month_passes():

    df = pd.DataFrame({
        'date': pd.to_datetime(['2020-01-11', '2020-02-12', '2020-03-13']),
        'amount': [11.1, 22.2, 33.3],
        'desc': ['costa coffee', 'waitrose', 'pure gym']
    })

    actual = cleaners.drop_last_month(df)

    expected = pd.DataFrame({
        'date': pd.to_datetime(['2020-01-11', '2020-02-12']),
        'amount': [11.1, 22.2],
        'desc': ['costa coffee', 'waitrose']
    })

    pd.testing.assert_frame_equal(actual, expected)
