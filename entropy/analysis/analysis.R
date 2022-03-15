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


# Load data ------------------------------------------------------------------------

dt = read_analysis_data()
names(dt)



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
  
  user_id = 'User id',
  month = 'Calendar month',
  
  spend_communication = 'Spend communication',
  spend_finance = 'Spend finance',
  spend_hobbies = 'Spend hobbies',
  spend_household = 'Spend household',
  spend_other_spend = 'Spend other',
  spend_motor = 'Spend motor',
  spend_retail = 'Spend retail',
  spend_services = 'Spend services',
  spend_travel = 'Spend travel',
  is_female = 'Female',
  age = 'Age',
  year_income = 'Year income'
))




# Effect on sa inflows -------------------------------------------------------------------------

# Variables

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
  'loan_repmt'
)

controls = c(fin_behav, planning, hh_chars)

setFixest_fml(
  ..entropy = c('entropy_tag_z', 'entropy_tag_sz')
)


# FE specifications
etable(
  fixest::feols(xpd(
    has_sa_inflows ~ ..entropy + ..controls | csw0(user_id, month),
    ..controls = controls), data=dt
  ), 
  title = 'FE specifications', 
  # tex = T,
  # file=file.path(TABDIR, 'reg_sw0.tex'),
  fontsize = 'tiny',
  label = 'tab:reg_fe',
  replace = T,
  order = c('!Entropy')
)



# FE specifications
etable(
  fixest::feols(xpd(
    has_sa_inflows ~ + ..entropy + ..controls | csw0(user_id, month),
    ..controls = controls), data=dt
  ), 
  title = 'FE specifications', 
  # tex = T,
  # file=file.path(TABDIR, 'reg_sw0.tex'),
  fontsize = 'tiny',
  label = 'tab:reg_fe',
  replace = T,
  order = c('!Entropy')
)


# Controls added one-by-one
etable(
  fixest::feols(has_sa_inflows ~ ..entropy + sw0(
    # fin behaviour
    has_reg_sa_inflows,
    prop_credit,
    month_spend,
    # planning (not yet implemented)
    # hh characteristics
    is_urban,
    month_income,
    has_regular_income,
    has_month_income,
    loan_repmt,
    pdloan_repmt
  ) | user_id + month, data=dt, vcov = 'cluster'),
  title = 'Controls included one-by-one', 
  # tex = T,
  # file=file.path(TABDIR, 'reg_sw0.tex'),
  fontsize = 'tiny',
  label = 'tab:reg_sw0',
  replace = T
)

# Controls added cumulatively
etable(
  fixest::feols(has_sa_inflows ~ ..entropy + csw0(
    # fin behaviour
    has_reg_sa_inflows,
    prop_credit, 
    month_spend,
    # planning (not yet implemented)
    # hh characteristics
    is_urban,
    month_income,
    has_regular_income,
    has_month_income,
    loan_repmt,
    pdloan_repmt
  ) | user_id + month, data=dt, vcov = 'cluster'), 
  title = 'Controls included cumulatively', 
  # tex = T,
  # file=file.path(TABDIR, 'reg_csw0.tex'),
  fontsize = 'tiny',
  label = 'tab:reg_csw0',
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


# Muggleton et al. (2020) replication ---------------------------------------------

# Replicating tables S20 (without FE) and S40 (with FE) in muggleton2020evidence

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
  fixest::feols(xpd(
    id ~ + sw(entropy_tag_sz, entropy_tag_z) + ..controls | sw0(user_id + month),
    ..controls = muggleton_controls), data=dt
  ),
  title = 'Muggleton et al. (2020) replication',
  order = c('Entropy', '!(Intercept)'),
  # tex = T,
  # file=file.path(TABDIR, 'reg_muggleton2020_replication.tex'),
  fontsize = 'normal',
  label = 'tab:muggleton2020_replication',
  
  replace = T
)

