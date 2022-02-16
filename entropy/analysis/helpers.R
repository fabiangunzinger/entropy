Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

library(aws.s3)

read_analysis_data <- function() {
  fn = 'analysis_XX7.csv'
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  df = aws.s3::s3read_using(data.table::fread, object=fp)
  df$month <- factor(df$month)
  return(df)
}
