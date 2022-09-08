library(data.table)
library(glue)
library(fixest)

Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/src/analysis')
source('../helpers/helpers.R')


df = read_analysis_data("XX0")
names(df)

setFixest_etable(
  postprocess.tex = set_font,
  se.below = T,
  digits = 'r3',
  coefstat = 'confint',
  style.tex = style.tex(
    main = "base",
    tpt = TRUE,
    notes.tpt.intro = '\\footnotesize'
  )
)

setFixest_dict(c(
  has_sa_inflows = "Has savings",
  sa_inflows = "Savings accounts inflows",
  sa_outflows = "Savings accounts outflows",
  sa_netflows = "Savings accounts net-inflows",
  
  entropy_tag_z = "Entropy (9 cats)",
  entropy_tag_sz = "Entropy (9 cats, smooth)",
  entropy_tag_spend_z = "Entropy (48 cats)",
  entropy_tag_spend_sz = "Entropy (48 cats, smooth)",
  entropy_merchant_z = "Entropy (merchant)",
  entropy_merchant_sz = "Entropy (merchant, smooth)",
  entropy_groc_z = "Entropy (groceries)",
  entropy_groc_sz = "Entropy (groceries, smooth)",
  
  pct_credit = "Paid with credit (%)",
  month_spend = 'Month spend',
  is_urban = 'Urban',
  is_female = 'Female',
  age = 'Age',
  year_income = "Year income",
  month_income = "Month income",
  has_regular_income = 'Has regular income',
  has_month_income = 'Has income in month',
  income_var = "Income variability",
  has_loan_repmt = 'Loan repayment',
  has_pension = 'Pension',
  has_benefits = 'Benefits',
  has_mortgage_pmt = 'Mortgage payment',
  has_rent_pmt = 'Rent payment',
  
  user_id = 'User id',
  ym = 'Calendar month',
  
  txns_count_spend = 'N',
  nunique_tag_spend = 'Cnz',
  std_tag_spend = 'Counts std all',
  avg_spend = 'Average spend'
))

setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..exog = ~sw(entropy_tag_spend_z, entropy_tag_spend_sz),
  ..comps = ~mvsw(entropy_tag_spend_z, avg_spend + nunique_tag_spend + std_tag_spend),
  ..controls = c(
  # fin behaviour
  # 'pct_credit',
  'month_spend',
  grep('^spend_', names(data), value = T),
  # planning - tbd
  # household / individual characteristics
  # 'is_urban',
  'month_income',
  'has_month_income',
  'income_var'
  # 'has_rent_pmt',
  # 'has_mortgage_pmt',
  # 'loan_repmt',
  # 'has_benefits'
  ),
  ..fe = ~user_id + ym
)



# Effect of entropy ---------------------------------------------------------------

endogs <- c("has_sa_inflows")

for (endog in endogs) {
  
  # unsmoothed entropy
  exog <- grep('entropy_.*_z$', names(dt), value = T)  
  print(
    etable(
      fixest::feols(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym), df),
      # fixest::feols(xpd(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym),
      #                   ..controls = controls), data=data),
    title = glue('{endog} on unsmoothed entropy'),
    order = c('[Ee]ntropy', '!(Intercept)')
    # ,
    # notes = c(note),
    # tex = T,
    # fontsize = 'tiny',
    # file=file.path(TABDIR, glue('reg_{endog}.tex')),
    # label = glue('tab:reg_{endog}'),
    # replace = T
    )
  )
  
  # smoothed entropy
  exog <- grep('entropy_.*_sz$', names(dt), value = T)
  print(
    etable(
      fixest::feols(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym), df),
      title = glue('{endog} on smoothed entropy'),
      order = c('[Ee]ntropy', '!(Intercept)')
      # ,
      # notes = c(note),
      # tex = T,
      # fontsize = 'tiny',
      # file=file.path(TABDIR, glue('reg_{endog}_s.tex')),
      # label = glue('tab:reg_{endog}_s'),
      # replace = T
    )
  )
}
  

