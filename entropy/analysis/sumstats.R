setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(stargazer)

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 
SAMPLE = '777'


dt = read_txn_data(SAMPLE)
head(dt)


# txn data

stargazer(
  dt,
  type = 'text'
  # out = file.path(TABDIR, 'sumstats.tex')
)


