import argparse
import os
import platform

import pandas as pd
import s3fs

from entropy import config


class BucketManager:
    """Helper class to easily manage project bucket.
    
    Instantiate manager with a bucket name, and it will
    automatically set up a file system instance with the
    appropriate aws profile.
    """
    
    def __init__(self, bucket_name):
        self.basepath = os.path.join('s3://', bucket_name)
        self.profile = config.aws_profile
        self.fs = s3fs.S3FileSystem(profile = self.profile)
    
    def list_raw(self):
        path = os.path.join(self.basepath, 'raw')
        display(self.fs.ls(path))
        
    def list_clean(self):
        path = os.path.join(self.basepath, 'clean')
        display(self.fs.ls(path))

    def list(self, path=None):
        if not path:
            path = os.path.join(self.basepath)
        else:
            path = os.path.join(self.basepath, path)
        display(self.fs.ls(path))



def s3read_csv(path, profile=config.aws_profile, **kwargs):
    """Read from s3 path."""
    options = dict(storage_options=dict(profile=profile))
    return pd.read_csv(path, **options, **kwargs)


def s3write_csv(df, path, profile=config.aws_profile, **kwargs):
    """Write df to s3 path."""
    options = dict(storage_options=dict(profile=profile))
    df.to_csv(path, index=False, **options, **kwargs)
    print(f'{path} (of shape {df.shape}) written.')
    return df


def s3read_parquet(path, profile=config.aws_profile, **kwargs):
    """Read from s3 path."""
    options = dict(storage_options=dict(profile=profile))
    return pd.read_parquet(path, **options, **kwargs)


def s3write_parquet(df, path, profile=config.aws_profile, **kwargs):
    """Write df to s3 path."""
    options = dict(storage_options=dict(profile=profile))
    df.to_parquet(path, index=False, **options, **kwargs)
    print(f'{path} (of shape {df.shape}) written.')
    return df


def s3fetch_nspl(**kwargs):
    """Fetch NSPL area lookup table."""
    nspl_version = 'NSPL_AUG_2020_UK'
    path = f's3://3di-data-ons/nspl/{nspl_version}/clean/'
    fn = f'lookup_{nspl_version.lower()}.parquet'
    fp = os.path.join(path, fn)
    return s3read_parquet(fp)


