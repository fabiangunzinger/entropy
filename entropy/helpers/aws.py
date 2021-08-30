import argparse
import os
import platform
import pandas as pd
import s3fs


def get_aws_profile():
    """Return name of AWS profile to use for S3 access."""
    if platform.node() == 'FabsMacBook.local':
        profile = 'tracker-fgu'

    return profile


class bucket_manager:
    """Helper class to easily manage project bucket.
    
    Instantiate manager with a bucket name, and it will
    automatically set up a file system instance with the
    appropriate aws profile, using `get_aws_profile`.
    """
    
    def __init__(self, bucket_name):
        self.basepath = os.path.join('s3://', bucket_name)
        self.profile = get_aws_profile()
        self.fs = s3fs.S3FileSystem(profile = self.profile)
    
    def list_raw(self):
        path = os.path.join(self.basepath, 'raw')
        display(self.fs.ls(path))
        
    def list_clean(self):
        path = os.path.join(self.basepath, 'clean')
        display(self.fs.ls(path))


def s3read_csv(path, profile=None, **kwargs):
    """Read from s3 path.

    Uses appropriate aws profile as specified in `get_aws_profile`.
    """
    if profile is None:
        profile = get_aws_profile()
    options = dict(storage_options=dict(profile=profile))

    df = pd.read_csv(path, **options, **kwargs)

    return df


def s3write_csv(df, path, profile=None, **kwargs):
    """Write df to s3 path.

    Uses appropriate aws profile as specified in `get_aws_profile`.
    """
    if profile is None:
        profile = get_aws_profile()
    options = dict(storage_options=dict(profile=profile))

    df.to_csv(path, index=False, **options, **kwargs)
    print(f'{path} (of shape {df.shape}) written.')

    return df


def s3read_parquet(path, profile=None, **kwargs):
    """Read from s3 path.

    Uses appropriate aws profile as specified in `get_aws_profile`.
    """
    if profile is None:
        profile = get_aws_profile()
    options = dict(storage_options=dict(profile=profile))

    df = pd.read_parquet(path, **options, **kwargs)

    return df


def s3write_parquet(df, path, profile=None, **kwargs):
    """Write df to s3 path.

    Uses appropriate aws profile as specified in `get_aws_profile`.
    """
    if profile is None:
        profile = get_aws_profile()
    options = dict(storage_options=dict(profile=profile))

    df.to_parquet(path, index=False, **options, **kwargs)
    print(f'{path} (of shape {df.shape}) written.')

    return df


def s3fetch_ons():
    """Fetch ONS area lookup table."""
    nspl_version = 'NSPL_AUG_2020_UK'

    path = f's3://3di-data-ons/nspl/{nspl_version}/clean/'
    fn = f'lookup_{nspl_version.lower()}.parquet'
    fp = os.path.join(path, fn)

    ons = s3read_parquet(fp)

    return ons


