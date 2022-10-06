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
  "^nunique_tag_spend$",
  "^nunique_tag$",
  "^nunique_merchant$"
)

varlabs <- c(
  "Month income (\\pounds'000)",
  "Has income in month",
  "Makes savings txns.",
  "Month spend (\\pounds'000)",
  "Age (years)",  
  "Female",
  "Urban",
  "Unique categories (9)",
  "Unique categories (48)",
  "Unique categories (Merch.)"
)


# Workaround to handle pounds sign. See link below.
# https://github.com/markwestcott34/stargazer-booktabs/issues/3
tab <- stargazer(
  df,
  summary.stat = c('mean', 'sd', 'min', 'p25', 'median', 'p75', 'max'),
  digits = 2,
  keep = vars,
  covariate.labels = varlabs,
  float = FALSE
)
tabname <- 'sumstats.tex'
cat(tab, sep = '\n', file = file.path(TABDIR, tabname))

