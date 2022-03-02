Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(data.table)
library(estimatr)
library(fixest)
library(modelsummary)
library(plm)
library(purrr)
library(stargazer)


# Load data ------------------------------------------------------------------------

dt = read_analysis_data()
names(dt)


# Global settings ------------------------------------------------------------------

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

setFixest_dict(c(
  # entropy = "Entropy",
  has_reg_sa_inflows = "Regular savings"
))

setFixest_etable(
  se.below = T,
  style.tex = style.tex(
    "base"
  )
)


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
  'loan_repmt',
  'pdloan_repmt'
  )

controls = c(fin_behav, planning, hh_chars)

setFixest_fml(
  ..entropy = 'entropy_tag_sst'
)


# FE specifications
etable(
  fixest::feols(xpd(
    has_sa_inflows ~ ..entropy + ..controls | csw0(user_id, month),
    ..controls = controls), data=dt
  ), 
  title = 'FE specifications', 
  # tex = T,
  fontsize = 'tiny',
  label = 'tab:reg_fe',
  # file=file.path(TABDIR, 'reg_sw0.tex'),
  replace = T
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
