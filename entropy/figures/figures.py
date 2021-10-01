"""
Create appendix figures.

"""
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from entropy import config


def income_distribution():
    """Plots histogram of annual incomes."""
    df = pd.read_parquet('~/tmp/entropy_777.parquet')
    incomes = df.groupby(['user_id', df.date.dt.year]).income.first()
    fig = sns.displot(incomes, aspect=2)
    fp = os.path.join(config.FIGDIR, 'income_distribution.png')
    plt.savefig(fp)


if __name__ == '__main__':
    income_distribution()
    
