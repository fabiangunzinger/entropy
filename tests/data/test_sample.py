import pandas as pd
import pytest

import entropy.data.cleaners as cl
from tests.data.fixtures import mdb1


def test_drop_first_and_last_month_passes(mdb1):

    actual = cl.drop_first_and_last_month(mdb1)

    expected = pd.DataFrame(
        {
            "user_id": [1],
            "date": pd.to_datetime(["2020-02-12"]),
            "amount": [22.2],
            "desc": ["waitrose"],
        }, index=[1]
    )

    pd.testing.assert_frame_equal(actual, expected)
