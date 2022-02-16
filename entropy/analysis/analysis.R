Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(data.table)
library(fixest)
library(modelsummary)
library(plm)
library(stargazer)

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 


df = read_analysis_data()

m1 <- plm(has_sa_inflows ~ entropyz + month,
          data=df, index = c('user_id'))

m2 <- plm(has_sa_inflows ~ entropyz + month_spend + month,
          data=df, index = c('user_id'))

m3 <- plm(has_sa_inflows ~ entropyz + month_spend + month_income + month,
          data=df, index = c('user_id'))

m4 <- plm(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend + month,
          data=df, index = c('user_id'))

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
  label = 'tab:main_results',
  # font.size = 'footnotesize',
  out=file.path(TABDIR, 'main_results.tex')
)


# extensions

models = list(
  'Unclustered' = feols(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend | user_id + month,
                        data=df),
  
  'Clustered' = feols(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend | user_id + month, "cluster",
                      data=df)
)

modelplot(models)

