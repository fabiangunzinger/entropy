Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

library(arrow)
library(aws.s3)
library(data.table)
library(stargazer)
library(plm)

TABDIR = '/Users/fgu/dev/projects/entropy/output/tables' 


read_analysis_data <- function() {
  fn = 'analysis_XX7.parquet'
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  data = aws.s3::s3read_using(arrow::read_parquet, object=fp)
  return(setDT(data, keep.rownames = TRUE))
}

df = read_analysis_data()

df$month <- factor(df$month)

m1 <- plm(has_sa_inflows ~ entropyz + month,
          data=df,
          index = c('user_id'),
          model = 'within',
          )

m2 <- plm(has_sa_inflows ~ entropyz + month_spend + month,
          data=df,
          index = c('user_id'),
          model = 'within',
)

m3 <- plm(has_sa_inflows ~ entropyz + month_spend + month_income + month,
          data=df,
          index = c('user_id'),
          model = 'within',
)

m4 <- plm(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_household + spend_retail + spend_other_spend + month,
          data=df,
          index = c('user_id'),
          model = 'within',
)

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
  font.size = 'normal',
  out=file.path(TABDIR, 'main_results.tex')
)


