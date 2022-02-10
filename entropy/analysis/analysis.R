Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

library(arrow)
library(aws.s3)
library(data.table)
library(plm)



read_analysis_data <- function() {
  fn = 'analysis_XX7.parquet'
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  data = aws.s3::s3read_using(arrow::read_parquet, object=fp)
  return(setDT(data, keep.rownames = TRUE))
}

df = read_analysis_data()
df