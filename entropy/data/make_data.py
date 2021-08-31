#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import contextlib
import cProfile
import os
import pstats
import re
import smart_open
import sys
import s3fs
import tempfile
import time

from concurrent import futures
from functools import wraps
import pandas as pd
from tqdm import tqdm
from memory_profiler import profile

from src import config
from . import (
    selection_table,
    save_selection_table,
    OrderedCounter,
    cleaner_funcs,
    selector_funcs,
    read_raw
)


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
        print(f'Time: {diff:.2f} {unit}')
        return result
    return wrapper


@timer
def split_file(filepath, dir):
    """Split file into pieces based on first digit of user id."""
    with smart_open.open(filepath, 'rt') as source:
        with contextlib.ExitStack() as stack:
            targets = {}
            for n in range(1, 10):
                fp = os.path.join(dir, f'{n}.csv')
                targets[str(n)] = stack.enter_context(open(fp, 'a'))
            header = source.readline()
            for f in targets.values():
                f.write(header)
            RE = re.compile('^"(?P<txn_id>\d+)"\|"(?P<user_id>\d+)"')
            for line in source:
                user_id = RE.match(line).group('user_id')
                targets[user_id[0]].write(line)
            pieces = [f.path for f in os.scandir(dir)]
            return pieces


def clean_df(piece):
    """Clean a single piece."""
    funcs = cleaner_funcs + selector_funcs
    clean = read_raw(piece)
    for func in funcs:
        clean = func(clean)
    return clean


@timer
def clean_data(raw_pieces):
    """Clean raw pieces in parallel and combine."""
    with futures.ProcessPoolExecutor() as pool:
        todo = [pool.submit(clean_df, piece) for piece in raw_pieces]
        done = futures.as_completed(todo)
        done = tqdm(done, total=len(todo), ncols=95)
        sample_count = OrderedCounter()
        clean_pieces = []
        for future in done:
            piece, count = future.result()
            clean_pieces.append(piece)
            sample_count.update(count)
        vars = ['user_id', 'transaction_date']
        df = (pd.concat(clean_pieces)
              .reset_index(drop=True)
              .sort_values(vars))
        return df, sample_count


def save_data(df, sample):
    name = f'data_{sample}.parquet'
    path = os.path.join(config.TEMPDIR, name)
    df.to_parquet(path)


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'sample', help='raw sample to be cleaned.')
    parser.add_argument(
        '-d', '--debug', action='store_true', help='run in debug mode.')
    parser.add_argument(
        '-p', '--profile', action='store_true', help='run in profiling mode.')
    parser.add_argument(
        '-mp', '--memprof', action='store_true', help='run memory profiler.')
    return parser.parse_args()


def main():
    global clean_data
    args = parse_args(sys.argv)
    fn = f'data_{args.sample}.csv'
    fp = os.path.join(config.TEMPDIR, fn)
    with tempfile.TemporaryDirectory() as tempdir:
        print('splitting file...')
        raw_pieces = split_file(fp, tempdir)
        raw_pieces = raw_pieces[:2] if args.debug else raw_pieces
        print('cleaning pieces...')
        if args.profile:
            cmd = 'clean_df(raw_pieces[5])'
            pr = os.path.join(config.PROFDIR, 'data_profile')
            cProfile.runctx(cmd, globals(), locals(), pr)
            return 'Profile saved.'
        df, count = clean_data(raw_pieces)
        table = selection_table(count)
        print(table)
        if not args.debug:
            save_selection_table(table, args.sample)
            save_data(df, args.sample)


if __name__ == '__main__':
    sys.exit(main())
