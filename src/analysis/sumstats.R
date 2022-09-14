# 
# Code to produce summary statistics table
# 


library(stargazer)

source('src/config.R')
source('src/helpers/helpers.R')


df = read_debug_data()

vars <- c(
  "^has_inflows$",
  "^month_spend$",
  "^is_urban$",
  "^is_female$",
  "^age$",
  "^year_income$",
  "^has_month_income$",
  "^has_inflows$",
  "^income_var$",
  "^nunique_tag_spend$",
  "^nunique_tag$",
  "^nunique_merchant$"
)


varlabs <- c(
  "Year income",
  "Income variability",
  "Has income in month",
  "Has savings",
  "Month spend",
  "Age",  
  "Female",
  "Urban",  
  "Unique categories (9)",
  "Unique categories (48)",
  "Unique categories (Merchants)"
)


tabname <- 'sumstats.tex'
stargazer(
  df,
  summary.stat = c('mean', 'sd', 'min', 'p25', 'median', 'p75', 'max'),
  digits = 2,
  keep = vars,
  covariate.labels = varlabs,
  title = 'Summary statistics',
  label = 'tab:sumstats',
  font.size = 'footnotesize',
  table.placement = "H",
  out = file.path(TABDIR, tabname)
)

