
def selection_table(dict):
    """Create sample selection table for data appendix."""
    df = pd.DataFrame(dict.items(), columns=['step', 'counts'])
    df[['step', 'metric']] = df.step.str.split('@', expand=True)
    df = (df.groupby(['step', 'metric'], sort=False)
          .counts.sum()
          .unstack('metric')
          .rename_axis(columns=None)
          .reset_index())
    ints = ['users', 'accs', 'txns']
    df[ints] = df[ints].applymap('{:,.0f}'.format)
    floats = ['value']
    df[floats] = df[floats].applymap('{:,.1f}'.format)
    df.columns = ['', 'Users', 'Accounts', 'Transactions', 'Value (\pounds M)']
    return df


def save_selection_table(table, sample):
    """Export sample selection table."""
    name = f'sample_selection_{sample}.tex'
    fp = os.path.join(config.TABDIR, name)
    with pd.option_context('max_colwidth', None):
        with open(fp, 'w') as f:
            f.write(table.to_latex(index=False, escape=False,
                                   column_format='lrrrr'))
