Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(data.table)
library(estimatr)
library(glue)
library(fixest)
library(modelsummary)
library(plm)
library(purrr)
library(stargazer)

# Settings -------------------------------------------------------------------------

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables'


# set fontsize of latex table produced by etable
set_font = function(x, fontsize){
  if(missing(fontsize)) return(x)
  dreamerr::check_arg_plus(fontsize, "match(tiny, scriptsize, footnotesize, small, normalsize, large, Large)")
  x[x == "%start:tab\n"] = paste0("\\begin{", fontsize, "}")
  x[x == "%end:tab\n"] = paste0("\\end{", fontsize, "}")
  return(x)
}
setFixest_etable(postprocess.tex = set_font)

setFixest_etable(
  se.below = T,
  style.tex = style.tex(
    "base"
  )
)

setFixest_dict(c(
  has_reg_sa_inflows = "Regular savings",
  
  entropy_tag_z = "Entropy (tag-based)",
  entropy_tag_sz = "Entropy (tag-based, smooth)",
  entropy_tag_auto_z = "Entropy (auto-tag-based)",
  entropy_tag_auto_sz = "Entropy (auto-tag-based, smooth)",
  entropy_merchant_z = "Entropy (merchant-based)",
  entropy_merchant_sz = "Entropy (merchant-based, smooth)",
  
  spend_communication = 'Spend communication',
  spend_finance = 'Spend finance',
  spend_hobbies = 'Spend hobbies',
  spend_household = 'Spend household',
  spend_other_spend = 'Spend other',
  spend_motor = 'Spend motor',
  spend_retail = 'Spend retail',
  spend_services = 'Spend services',
  spend_travel = 'Spend travel',
  prop_credit = 'Credit spend',
  month_spend = 'Month spend',

  is_urban = 'Urban',
  is_female = 'Female',
  age = 'Age',
  year_income = 'Year income',
  month_income = 'Month income (\'000)',
  has_regular_income = 'Regular income',
  has_month_income = 'Has income in month',
  has_loan_repmt = 'Loan repayment',
  
  user_id = 'User id',
  ym = 'Calendar month'
))


# Load data ------------------------------------------------------------------------

dt = read_analysis_data()
names(dt)




# New ------------------------------------------------------------------------------

endog = 'has_sa_inflows'
exog = c('entropy_tag_sz', 'entropy_tag_z')
fin_behav = c(
  'has_reg_sa_inflows',
  'prop_credit',
  'month_spend'
)
planning = c()
hh_chars = c(
  'is_urban',
  'month_income',
  'has_regular_income',
  'has_month_income',
  'has_loan_repmt'
)
controls = c(fin_behav, planning, hh_chars)


# FE specifications
etable(
  fixest::feols(
    xpd(
      ..endog ~ ..exog + ..controls | csw0(user_id, ym),
      ..endog = endog,
      ..controls = controls,
      ..exog = exog
    ),
    data=dt
  ), 
  title = 'FE specifications', 
  order = c('!(Intercept)'),
  tex = T,
  file=file.path(TABDIR, 'reg_entropy_savings_fe.tex'),
  fontsize = 'footnotesize',
  label = 'tab:reg_entropy_savings_fe',
  replace = T
)





# Effect of entropy on savings -----------------------------------------------------

endog = 'has_sa_inflows'
exog = c('entropy_tag_sz', 'entropy_tag_z')
fin_behav = c(
  'has_reg_sa_inflows',
  'prop_credit',
  'month_spend'
)
planning = c()
hh_chars = c(
  'is_urban',
  'month_income',
  'has_regular_income',
  'has_month_income',
  'has_loan_repmt'
)
controls = c(fin_behav, planning, hh_chars)


# FE specifications
etable(
  fixest::feols(
    xpd(
      ..endog ~ ..exog + ..controls | csw0(user_id, ym),
      ..endog = endog,
      ..controls = controls,
      ..exog = exog
    ),
    data=dt
  ), 
  title = 'FE specifications', 
  order = c('!(Intercept)'),
  tex = T,
  file=file.path(TABDIR, 'reg_entropy_savings_fe.tex'),
  fontsize = 'footnotesize',
  label = 'tab:reg_entropy_savings_fe',
  replace = T
)


# controls added one-by-one
etable(
  fixest::feols(
    xpd(
      ..endog ~ ..exog
        + sw0(
          # fin behav
          has_reg_sa_inflows,
          prop_credit,
          month_spend,
          # hh chars
          is_urban,
          month_income,
          has_regular_income,
          has_month_income,
          has_loan_repmt
        )
      | user_id + ym,
      ..endog = endog,
      ..controls = controls,
      ..exog = exog
    ),
    data=dt
  ), 
  title = 'FE specifications', 
  tex = T,
  file=file.path(TABDIR, 'reg_entropy_savings_obo.tex'),
  fontsize = 'footnotesize',
  label = 'tab:reg_entropy_savings_obo',
  replace = T
)

# Between vs within variation
entropy <- entropy_tag
a = dt[, .(g_mean = mean(entropy_tag), g_sd = sd(entropy_tag)), user_id]
within_var = mean(a$g_sd)
between_var = sd(a$g_mean)
total_var = sd(dt[[entropy]])
print(total_var)
print(within_var)
print(between_var)
print(within_var / between_var)


# Entropy with num-zero count
etable(
  fixest::feols(xpd(has_od_fees ~ csw(entropy_tag_size, nunique_tag) + ..controls  | user_id + ym, ..endog = endog, ..controls = controls, ..exog = exog), data=dt), 
  # title = 'FE specifications', 
  order = c('entropy', 'nunique')
  # tex = T,
  # file=file.path(TABDIR, 'reg_entropy_savings_fe.tex'),
  # fontsize = 'footnotesize',
  # label = 'tab:reg_entropy_savings_fe',
  # replace = T
)



# All entropy vars - tag only thus far
cat_vars = c('tag', 'auto_tag', 'merchant')

for (cat in cat_vars) {
  exog = names(dt)[grep(cat, names(dt))]
  print(exog)
}

etable(
  fixest::feols(
    xpd(
      ..endog ~ 
        sw(
          entropy_tag_size_z,
          entropy_tag_size_sz,
          entropy_tag_sum_z,
          entropy_tag_sum_sz,
          
          # entropy_tag_size_n,
          # 
          # entropy_tag_size_sn,
          # entropy_tag_sum,
          # entropy_tag_sum_n,
          # entropy_tag_sum_s,
          # entropy_tag_sum_sn
      )
      + ..controls | user_id + ym,
      ..endog = endog,
      ..controls = controls,
      ..exog = exog
    ),
    data=dt
  ), 
  # title = 'FE specifications', 
  order = c('entropy', '!(Intercept)')
  # tex = T,
  # file=file.path(TABDIR, 'reg_entropy_savings_fe.tex'),
  # fontsize = 'footnotesize',
  # label = 'tab:reg_entropy_savings_fe',
  # replace = T
)
  



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
  order = c('Entropy', '!(Intercept)'),
  tex = T,
  file=file.path(TABDIR, 'reg_entropy_odfees.tex'),
  fontsize = 'scriptsize',
  label = 'tab:reg_entropy_odfees',
  replace = T
)

