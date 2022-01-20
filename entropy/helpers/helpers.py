import argparse
import os
import time
from functools import wraps

from entropy import config
from entropy.helpers import aws


def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        diff = end - start
        unit = 'seconds'
        if diff > 60:
            diff = diff / 60
            unit = 'minutes'
        print(f'Time for {func.__name__:15}: {diff:.2f} {unit}')
        return result
    return wrapper


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true',
                        help='Run test version.')
    parser.add_argument('--nowrite', action='store_true',
                        help='Do not write output to disk.')
    parser.add_argument('--nrows', type=int,
                        help='Number of rows to read per file.')
    return parser.parse_args()


