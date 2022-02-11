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

m4 <- plm(has_sa_inflows ~ entropyz + month_income + spend_communication + spend_services + spend_finance + spend_motor + spend_travel + spend_hobbies + spend_other_spend + spend_household + spend_retail + user_id + month,
          data=df,
          index = c('user_id'),
          model = 'within',
)


stargazer(m1, m2, m3, m4,
          title='Main results', 
          out=file.path(TABDIR, 'main_results.tex'),
          omit.stat=c("LL","ser","f"),
          no.space=TRUE,
          style = 'qje'
          )


