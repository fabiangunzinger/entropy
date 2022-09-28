# 
# Code to produce summary statistics table
# 


library(stargazer)

source('./src/config.R')
source('./src/helpers/helpers.R')


df = read_analysis_data()

names(df)

vars <- c(
  "^has_inflows$",
  "^month_spend$",
  "^is_urban$",
  "^is_female$",
  "^age$",
  "^month_income$",
  "^has_month_income$",
  "^has_inflows$",
  "^nunique_tag_spend$",
  "^nunique_tag$",
  "^nunique_merchant$",
)

varlabs <- c(
  "Month income",
  "Has income in month",
  "Makes savings txns.",
  "Month spend",
  "Age",  
  "Female",
  "Urban",  
  "Unique categories (9)",
  "Unique categories (48)",
  "Unique categories (Merch.)"
)


tabname <- 'sumstats.tex'
stargazer(
  df,
  summary.stat = c('mean', 'sd', 'min', 'p25', 'median', 'p75', 'max'),
  digits = 2,
  float = FALSE,
  keep = vars,
  covariate.labels = varlabs,
  out = file.path(TABDIR, tabname)
)

