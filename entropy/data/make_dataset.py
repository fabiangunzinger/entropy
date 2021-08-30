# -*- coding: utf-8 -*-
# import click
import logging
# from pathlib import Path
# from dotenv import find_dotenv, load_dotenv


import pandas as pd
# import habits.helpers.aws as aws


def read_huq(fp, **kwargs):
    """Read unprocessed huq data."""
    df = aws.s3read_csv(fp, parse_dates=['timestamp'], **kwargs)

    # convert strings to lowercase
    strings = df.select_dtypes('object').columns
    df[strings] = df[strings].apply(lambda x: x.str.lower())

    # create additional variables
    df['date'] = pd.to_datetime(df.timestamp.dt.date)

    return df

def main():
    logging.info('start')
    1 + 6
    logging.info('end')

# @click.command()
# @click.argument('input_filepath', type=click.Path(exists=True))
# @click.argument('output_filepath', type=click.Path())
# def main(input_filepath, output_filepath):
#     """ Runs data processing scripts to turn raw data from (../raw) into
#         cleaned data ready to be analyzed (saved in ../processed).
#     """
#     logger = logging.getLogger(__name__)
#     logger.info('making final data set from raw data')


if __name__ == '__main__':
    # log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    # project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    # load_dotenv(find_dotenv())
    # main()
    main()


