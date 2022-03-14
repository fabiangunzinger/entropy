

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

setFixest_dict(c(
  entropy_tag_z = "Entropy",
  entropy_tag_sz = "Entropy (smooth)",
  has_reg_sa_inflows = "Regular savings"
))

setFixest_etable(
  se.below = T,
  style.tex = style.tex(
    "base"
  )
)

controls_fe = c(
  'spend_communication',
  'spend_finance',
  'spend_hobbies',
  'spend_household',
  'spend_other_spend',
  'spend_motor',
  'spend_retail',
  'spend_services',
  'spend_travel'
)

controls = c(
  controls_fe,
  'female',
  'age',
  'year_income'
)

setFixest_fml(
  ..entropy = c('entropy_tag_z')
  )


etable(
  fixest::feols(xpd(
    id ~ + sw(entropy_tag_sz, entropy_tag_z) + ..controls | sw0(user_id + month),
    ..controls = controls), data=dt
  ),
  title = 'Muggleton et al. (2020) replication', 
  tex = T,
  fontsize = 'normal',
  label = 'tab:muggleton2020_replication',
  file=file.path(TABDIR, 'reg_muggleton2020_replication.tex'),
  replace = T, 
  order = c('Entropy', '!(Intercept)')
)
