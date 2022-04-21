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

read_final_users_data <- function(sample='X77') {
  # cannot load txn data for full sample into memory, so using txns
  # from users in sample that are part of the final analysis data
  dta <- read_analysis_data()
  dtt <- read_txn_data(sample)
  dta_users <- unique(dta$user_id)
  dt <- dtt[user_id %in% dta_users]
}

# set fontsize of latex table produced by etable
set_font = function(x, fontsize){
  if(missing(fontsize)) return(x)
  dreamerr::check_arg_plus(fontsize, "match(tiny, scriptsize, footnotesize, small, normalsize, large, Large)")
  x[x == "%start:tab\n"] = paste0("\\begin{", fontsize, "}")
  x[x == "%end:tab\n"] = paste0("\\end{", fontsize, "}")
  return(x)
}


facet_kdes <- function(regex, ncol = 3) {
  vars <- grep(regex, names(dt), value = T, perl = T)
  data <- melt(dt[, ..vars], measure.vars = vars)
  ggplot(data) +
    geom_density(aes(value)) +
    facet_wrap(~variable, ncol = ncol, scales = 'free')
}