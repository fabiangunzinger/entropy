Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

library(arrow)
library(aws.s3)
library(data.table)
library(fasttime)
library(glue)

read_analysis_data <- function(sample = 'XX7') {
  fn = glue('analysis_{sample}.parquet')
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  dt = setDT(aws.s3::s3read_using(arrow::read_parquet, object=fp))
  return(dt)
}

read_txn_data <- function(sample = 'X77') {
  fn = glue('txn_{sample}.parquet')
  bucket = 's3://3di-project-entropy'
  fp = file.path(bucket, fn)
  dt = setDT(aws.s3::s3read_using(arrow::read_parquet, object=fp))
  dt[, date := as.Date(date)]
  return(dt)
}

# set fontsize of latex table produced by etable
set_font = function(x, fontsize){
  if(missing(fontsize)) return(x)
  dreamerr::check_arg_plus(fontsize, "match(tiny, scriptsize, footnotesize, small, normalsize, large, Large)")
  x[x == "%start:tab\n"] = paste0("\\begin{", fontsize, "}")
  x[x == "%end:tab\n"] = paste0("\\end{", fontsize, "}")
  return(x)
}