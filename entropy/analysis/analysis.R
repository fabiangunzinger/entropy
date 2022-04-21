library(data.table)
library(estimatr)
library(gglm)
library(glue)
library(fixest)
library(modelsummary)
library(plm)
library(purrr)
library(stargazer)
library(xtable)

source('helpers.R')
Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables'

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
  
  spend_communication = 'Spend communication',
  spend_finance = 'Spend finance',
  spend_hobbies = 'Spend hobbies',
  spend_household = 'Spend household',
  spend_other_spend = 'Spend other',
  spend_motor = 'Spend motor',
  spend_retail = 'Spend retail',
  spend_services = 'Spend services',
  spend_travel = 'Spend travel',
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
  
  txns_count_spend = 'Spend txns',
  nunique_tag_spend = 'Unique categories',
  ssd_tag_spend = 'Category count variation'
))


dt = read_analysis_data()
# temporarily truncate manually. decide how to handle.
data <- dt[sa_inflows <= 3000 & sa_outflows <= 3000]
names(data)

note <- "Notes: Spend and income variables are in \\pounds'000."
endogs = c('has_sa_inflows', 'sa_inflows', 'sa_netflows', 'sa_outflows')
cat_spends <- grep('spend_(?!month)', names(dt), value = T, perl = T)
controls = c(
  # fin behaviour
  'pct_credit',
  'month_spend',
  # planning - tbd
  # hh / ind chars
  'is_urban',
  'month_income',
  'has_month_income',
  'income_var',
  'has_rent_pmt',
  'has_mortgage_pmt',
  'has_loan_repmt',
  'has_benefits'
)


# Explore effect of nunique and ssd ------------------------------------------------

setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..exog = ~entropy_tag_spend_z,
  ..exog_s = ~entropy_tag_spend_z + entropy_tag_spend_sz,
  ..comps = ~sw0(txns_count_spend,
                 nunique_tag_spend,
                 ssd_tag_spend,
                 txns_count_spend + nunique_tag_spend + ssd_tag_spend),
  ..fe = ~user_id + ym
)

etable(
  fixest::feols(..endog ~ ..exog + ..comps | ..fe, data=data),
  fixest::feols(..endog ~ ..exog_s + ..comps | ..fe, data=data),
  title = glue('Entropy exploration'),
  order = c('[Ee]ntropy'),
  notes = c(note),
  tex = T,
  fontsize = 'tiny',
  file=file.path(TABDIR, glue('reg_has_sa_inflows_explore.tex')),
  label = glue('tab:reg_has_sa_inflows_explore'),
  replace = T
)

setFixest_fml(
  ..endog = ~entropy_tag_spend_z,
  ..exog = ~sw(entropy_tag_spend_sz,
                txns_count_spend,
                nunique_tag_spend,
                ssd_tag_spend,
                entropy_tag_spend_sz + txns_count_spend + nunique_tag_spend + ssd_tag_spend),
  ..fe = ~user_id + ym
)

etable(
  fixest::feols(..endog ~ ..exog | ..fe, data=data),
  title = glue('Entropy exploration'),
  order = c('[Ee]ntropy'),
  notes = c(note),
  tex = T,
  fontsize = 'tiny',
  file=file.path(TABDIR, glue('reg_has_sa_inflows_explore.tex')),
  label = glue('tab:reg_has_sa_inflows_explore'),
  replace = T
)



cor(data[, .(entropy_tag_spend_z, entropy_tag_spend_sz, txns_count_spend, nunique_tag_spend, ssd_tag_spend)])


# Effect of entropy on spending ----------------------------------------------------

for (endog in endogs) {
  
  # unsmoothed entropy
  exog <- grep('entropy_.*_z$', names(dt), value = T)  
  print(
    etable(
      fixest::feols(xpd(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym),
                        ..controls = controls), data=data),
    title = glue('{endog} on unsmoothed entropy'),
    order = c('[Ee]ntropy', '!(Intercept)'),
    notes = c(note),
    tex = T,
    fontsize = 'tiny',
    file=file.path(TABDIR, glue('reg_{endog}.tex')),
    label = glue('tab:reg_{endog}'),
    replace = T
    )
  )
  
  # smoothed entropy
  exog <- grep('entropy_.*_sz$', names(dt), value = T)  
  print(
    etable(
      fixest::feols(xpd(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym),
                        ..controls = controls), data=data),
      title = glue('{endog} on smoothed entropy'),
      order = c('[Ee]ntropy', '!(Intercept)'),
      notes = c(note),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{endog}_s.tex')),
      label = glue('tab:reg_{endog}_s'),
      replace = T
    )
  )
}
  


# Effect of entropy on overdraft fees ----------------------------------------------

muggleton_controls = c(
  'spend_communication',
  'spend_finance',
  'spend_hobbies',
  'spend_household',
  'spend_other_spend',
  'spend_motor',
  'spend_retail',
  'spend_services',
  'spend_travel',
  'is_female',
  'age',
  'year_income'
)

etable(
  fixest::feols(
    xpd(
      has_od_fees ~ + sw(entropy_tag_sz, entropy_tag_z) + ..controls | sw0(user_id + ym),
      ..controls = muggleton_controls), data=dt
  ),
  title = 'Effect of entropy on overdraft fees',
  order = c('[Ee]ntropy', '!(Intercept)'),
  tex = T,
  file=file.path(TABDIR, 'reg_entropy_odfees.tex'),
  fontsize = 'scriptsize',
  label = 'tab:reg_entropy_odfees',
  replace = T
)


# Intertemporal analysis (dev) ------------------------------------------------------

dtt <- read_final_users_data()

# sum of squared differences in auto_tag counts to previous month
d <- na.omit(dtt[, .N, .(user_id, ym, tag_auto)])
d[, tag_auto := gsub('[[:punct:]]| ', '', tag_auto)]
d <- dcast(d, user_id + ym ~ tag_auto, value.var = 'N', fill = 0)
sq_diffs <- function(x) {
  abs(x - shift(x)) ** 2
}
vars <- setdiff(names(d), c('user_id', 'ym'))
d <- na.omit(d[, c(vars) := lapply(.SD, sq_diffs), by = user_id, .SDcols = vars])
d <- d[, .(rss = Reduce(`+`, .SD)), by = .(user_id, ym), .SDcols = 3:ncol(d)]


# merge with analysis data (for X77 sample only)

dt[d, on = .(user_id, ym)]
dt[d, on = .(user_id, ym)][, sa_inflows]
dd[, .(savings = sum(sa_inflows), rss = sum(rss)), user_id] ## there shouldnt be any nans!

