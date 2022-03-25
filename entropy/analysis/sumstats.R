setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(stargazer)

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 
SAMPLE = '777'


dt = read_analysis_data()
head(dt)

stargazer(
  dt,
  digits = 2,
  summary.stat = c('mean', 'sd', 'min', 'p25', 'median', 'p75', 'max'),
  type = 'text'
  
  # title = 'Summary statistics',
  # label = 'tab:sumstats',
  # font.size = 'scriptsize',
  # out = file.path(TABDIR, 'sumstats.tex')
)


