Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(data.table)
library(estimatr)
library(fixest)
library(modelsummary)
library(plm)
library(stargazer)

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 

dt = read_analysis_data()


# data prep ------------------------------------------------------------------------

divider <- function(x){
  return(x / 1000)
}
cols = grep('spend|income', names(dt), value = T)
dt[, (cols) := lapply(.SD, divider), .SDcols = cols]


m1 <- plm(has_sa_inflows ~ entropy + month,
          data=dt, index = c('user_id'))

m2 <- plm(has_sa_inflows ~ entropy + month_spend + month,
          data=dt, index = c('user_id'))

m3 <- plm(has_sa_inflows ~ entropy + month_spend + month_income + month,
          data=dt, index = c('user_id'))

m4 <- plm(has_sa_inflows ~ entropy + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend + month,
          data=dt, index = c('user_id'))

stargazer(
  m1, m2, m3, m4,
  type = 'text',
  title='Main results',
  covariate.labels = c(
    'Entropy',
    'Month spend',
    'Month income',
    'Spend communication',
    'Spend services',
    'Spend finance',
    'Spend motor',
    'Spend travel',
    'Spend hobbies',
    'Spend household',
    'Spend retail',
    'Spend other'
  ),
  report = 'vc*t',
  keep.stat = c('n', 'rsq'),
  no.space = TRUE,
  dep.var.labels.include = FALSE,
  dep.var.caption = "Dependent variable: has transfers into savings account",
  omit = '^month\\d+$',
  add.lines = list(
    c('Individual fixed effects', 'Yes', 'Yes', 'Yes', 'Yes'),
    c('Month fixed effects', 'Yes', 'Yes', 'Yes', 'Yes')
  ),
  notes.align = 'l',
  notes.append = FALSE,
  notes.label = "",
  notes = "Note: Spend and income variables are in 000's. *p<0.1; **p<0.05; ***p<0.01.",
  label = 'tab:main_results'
  # font.size = 'footnotesize',
  # out=file.path(TABDIR, 'main_results.tex')
)



# estimatr 

m1 <- plm(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend + month,
          data=dt, index = c('user_id'))

m2 <- lm_robust(has_sa_inflows ~ entropyz, data = dt)


stargazer(
  m1, m2,
  type = 'text',
  title='Main results',
  covariate.labels = c(
    'Entropy',
    'Month spend',
    'Month income',
    'Spend communication',
    'Spend services',
    'Spend finance',
    'Spend motor',
    'Spend travel',
    'Spend hobbies',
    'Spend household',
    'Spend retail',
    'Spend other'
  ),
  report = 'vct',
  keep.stat = c('n', 'rsq'),
  no.space = TRUE,
  dep.var.labels.include = FALSE,
  dep.var.caption = "Dependent variable: has transfers into savings account",
  omit = '^month\\d+$',
  add.lines = list(
    c('Individual fixed effects', 'Yes', 'Yes', 'Yes', 'Yes'),
    c('Month fixed effects', 'Yes', 'Yes', 'Yes', 'Yes')
  ),
  notes.align = 'l',
  notes.append = FALSE,
  notes.label = "",
  notes = 'Note: ... *p<0.1; **p<0.05; ***p<0.01.',
  label = 'tab:main_results'
  # font.size = 'footnotesize',
)



# extensions

models = list(
  'Unclustered' = feols(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend | user_id + month,
                        data=dt),
  
  'Clustered' = feols(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend | user_id + month, "cluster",
                      data=dt)
)

modelplot(models)

