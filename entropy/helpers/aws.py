import argparse
import os
import platform

import pandas as pd
import s3fs

from entropy import config


def s3read_csv(path, profile=config.AWS_PROFILE, **kwargs):
    """Read from s3 path."""
    options = dict(storage_options=dict(profile=profile))
    return pd.read_csv(path, **options, **kwargs)


def s3write_csv(df, path, profile=config.AWS_PROFILE, **kwargs):
    """Write df to s3 path."""
    options = dict(storage_options=dict(profile=profile))
    df.to_csv(path, index=False, **options, **kwargs)
    print(f"{path} (of shape {df.shape}) written.")
    return df


def read_parquet(path, aws_profile=config.AWS_PROFILE, **kwargs):
    if path.startswith("s3"):
        options = dict(storage_options=dict(profile=aws_profile))
        return pd.read_parquet(path, **options, **kwargs)
    return pd.read_parquet(path, **kwargs)


def write_parquet(df, path, aws_profile=config.AWS_PROFILE, verbose=False, **kwargs):
    """Write df to s3 path."""
    if path.startswith("s3"):
        options = dict(storage_options=dict(profile=aws_profile))
        df.to_parquet(path, index=False, **options, **kwargs)
    else:
        df.to_parquet(path, index=False, **kwargs)
    if verbose:
        print(f"{path} (of shape {df.shape}) written.")
    return df


def s3fetch_nspl(**kwargs):
    """Fetch NSPL area lookup table."""
    nspl_version = "NSPL_AUG_2020_UK"
    path = f"s3://3di-data-ons/nspl/{nspl_version}/clean/"
    fn = f"lookup_{nspl_version.lower()}.parquet"
    fp = os.path.join(path, fn)
    return read_parquet(fp)
