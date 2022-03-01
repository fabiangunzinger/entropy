Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(data.table)
library(estimatr)
library(fixest)
library(modelsummary)
library(plm)
library(stargazer)

# set fontsize of latex table produced by etable
set_font = function(x, fontsize){
  if(missing(fontsize)) return(x)
  dreamerr::check_arg_plus(fontsize, "match(tiny, scriptsize, footnotesize, small, normalsize, large, Large)")
  x[x == "%start:tab\n"] = paste0("\\begin{", fontsize, "}")
  x[x == "%end:tab\n"] = paste0("\\end{", fontsize, "}")
  return(x)
}
setFixest_etable(postprocess.tex = set_font)


TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 

dt = read_analysis_data()







sw <- fixest::feols(has_sa_inflows ~ entropy + sw0(
  # fin behaviour
  has_reg_sa_inflows,
  prop_credit, 
  month_spend,
  
  # planning (not yet implemented)
  
  # hh characteristics
  age,
  is_urban,
  month_income,
  year_income,
  has_regular_income,
  has_month_income,
  has_benefits,
  has_pension,
  has_mortgage_pmt,
  has_rent_pmt,
  loan_funds,
  loan_repmt,
  pdloan_funds,
  pdloan_repmt
  ) | user_id + month, data=dt, vcov = 'cluster')

etable(
  sw, 
  se.below = T,
  title = 'Controls included one-by-one', 
  # tex = T,
  fontsize = 'tiny',
  style.tex = style.tex(
    main = 'aer'
  ),
  label = 'tab:reg_sw0',
  # file=file.path(TABDIR, 'reg_sw0.tex'),
  replace = T
)


csw <- fixest::feols(has_sa_inflows ~ entropyz + csw0(has_reg_sa_inflows, prop_credit, month_spend, month_income, has_regular_income, has_month_income, has_benefits, has_pension, has_mortgage_pmt, has_rent_pmt, loan_funds, loan_repmt, pdloan_funds, pdloan_repmt) | user_id + month, data=dt, vcov = 'cluster')


etable(
  csw, 
  se.below = T,
  title = 'Main result', 
  dict = c(
    month_income="Month income"
  ),
  tex = T,
  fontsize = 'tiny',
  label = 'tab:reg_csw0',
  file=file.path(TABDIR, 'reg_csw0.tex'),
  replace = T
)
