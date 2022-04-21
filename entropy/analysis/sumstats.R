library(stargazer)

source('helpers.R')
setwd('~/dev/projects/entropy/entropy/analysis')

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 


dt = read_analysis_data()
head(dt)

stargazer(
  dt,
  summary.stat = c('mean', 'sd', 'min', 'p25', 'median', 'p75', 'max'),
  title = 'Summary statistics',
  label = 'tab:sumstats',
  font.size = 'scriptsize',
  out = file.path(TABDIR, 'sumstats.tex')
)
