library(aws.s3)
library(glue)


read_s3parquet <- function(filepath) {
  # Wrapper to conveniently read parquet files from S3.
  data.frame(aws.s3::s3read_using(arrow::read_parquet, object=filepath))
}


read_analysis_data <- function(sample) {
  fn <- if (!missing(sample)) glue('entropy_{sample}.parquet') else 'entropy.parquet'
  fp <- file.path('s3://3di-project-entropy', fn)
  df <- data.frame(aws.s3::s3read_using(arrow::read_parquet, object=fp))
  num_users <- format(length(unique(df$user_id)), big.sep = ",")
  num_user_months <- format(nrow(df), big.sep = ",")
  print(fn)
  print(glue('Users: {num_users}; User-months: {num_user_months}'))
  return(df)
}


read_txn_data <- function(sample = 'X11') {
  fn <- glue('mdb_{sample}.parquet')
  bucket <- 's3://3di-data-mdb/clean/samples'
  fp <- file.path(bucket, fn)
  data.frame(aws.s3::s3read_using(arrow::read_parquet, object=fp)) %>% 
    mutate(date = as.Date(date))
}


read_txn_sample <- function(analysis_data, ...) {
  # Cannot load txn data for full sample into memory, so using txns
  # from users in X00 sample that are part of the analysis data
  txn_data <- read_txn_data(...)
  analysis_users <- unique(analysis_data$user_id)
  txn_data %>% filter(user_id %in% analysis_users)
}


read_lcfs <- function() {
  # Read ONS Living Cost and Food Survey 2018/19 wave and
  # calculate yearly household income and spending
  # Variable definitions:
  # P389p: Normal weekly disposable household income - anonymised
  # P600: COICOP: Total consumption expenditure
  fp <- 's3://3di-data-ons/lcfs/tab/2018_dvhh_ukanon.tab'
  df <- s3read_using(read.table, object = fp, sep = '\t', header = TRUE) %>% 
    select(wk_income = P389p, wk_spend = P600) %>% 
    transmute(
      yr_income = wk_income * 52,
      yr_spend = wk_spend * 52,
      source = 'LCFS'
    )
}


figure <- function(filepath, width=2000, height=1000, pointsize=30, ...) {
  # wrapper around png with custom settings
  png(
    file.path(FIGDIR, filepath),
    width = width,
    height = height,
    units = "px",
    pointsize = pointsize,
    ...
  )
}

entropy_vars <- function(df) {
  entropy_z <- grep('^entropy_(tag|merchant).*_z$', names(df), value = T)
  entropy_sz <- grep('^entropy_(tag|merchant).*_sz$', names(df), value = T)
  c(entropy_z, entropy_sz)
}


lagged_entropy_vars <- function(df) {
  entropy_z <- grep('^entropy_(tag|merchant).*_z_lag$', names(df), value = T)
  entropy_sz <- grep('^entropy_(tag|merchant).*_sz_lag$', names(df), value = T)
  c(entropy_z, entropy_sz)
}
