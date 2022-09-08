# 
# Code to produce summary statistics table
# 


library(stargazer)

source('./src/config.R')
source('./src/helpers/helpers.R')


df = read_analysis_data()


vars <- c(
  "^txns_count$",
  "^month_income$",
  "^inflows$",
  "^outflows$",
  "^netflows$",
  "^month_spend$", 
  "^age$",
  "^is_female$", 
  "^is_urban$",
  "^dspend$",
  "accounts_active"
  )

var_labs <- c(
  "Txn count",
  "Month income",
  "Savings account inflows",
  "Savings account outflows",
  "Savings account netflows",
  "Month spend", 
  "Age",
  "Female dummy", 
  "Urban dummy",
  "Discretionary spend",
  "Active accounts"
)


tabname <- 'sumstats.tex'
stargazer(
  df,
  summary.stat = c('mean', 'sd', 'min', 'p25', 'median', 'p75', 'max'),
  digits = 1,
  keep = vars,
  covariate.labels = var_labs,
  title = 'Summary statistics',
  label = 'tab:sumstats',
  font.size = 'footnotesize',
  table.placement = "H",
  out = file.path(TABDIR, tabname)
)

