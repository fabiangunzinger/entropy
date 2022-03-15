Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

library(aws.s3)
library(fasttime)
library(glue)

read_analysis_data <- function(sample = 'XX7') {
  fn = glue('analysis_{sample}.csv')
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  dt = aws.s3::s3read_using(data.table::fread, object=fp)
  dt[, date := fastPOSIXct(date)]
  return(dt)
}

read_txn_data <- function(sample = 'XX7') {
  fn = glue('txn_{sample}.csv')
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  dt = aws.s3::s3read_using(data.table::fread, object=fp)
  dt[, date := fastPOSIXct(date)]
  return(dt)
}

