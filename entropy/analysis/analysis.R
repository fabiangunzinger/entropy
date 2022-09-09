library(data.table)
library(glue)
library(fixest)

Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/src/analysis')
source('../helpers/helpers.R')
source('fixest_settings.R')


df = read_analysis_data("XX0")
names(df)


setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..exog = ~sw(entropy_tag_spend_z, entropy_tag_spend_sz),
  ..comps = ~mvsw(entropy_tag_spend_z, avg_spend + nunique_tag_spend + std_tag_spend),
  ..controls = c(
    # fin behaviour
    # 'pct_credit',
    'month_spend',
    grep('^spend_', names(data), value = T),
    # planning - tbd
    # household / individual characteristics
    # 'is_urban',
    'month_income',
    'has_month_income',
    'income_var'
    # 'has_rent_pmt',
    # 'has_mortgage_pmt',
    # 'loan_repmt',
    # 'has_benefits'
  ),
  ..fe = ~user_id + ym
)


# Effect of entropy ---------------------------------------------------------------

endogs <- c("has_inflows", "has_netflows", "inflows", "netflows", "investments", "dspend")

for (endog in endogs) {
  
  # unsmoothed entropy
  exog <- grep('entropy_.*_z$', names(dt), value = T)  
  print(
    etable(
      fixest::feols(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym), df),
      title = glue('{endog} on unsmoothed entropy'),
      order = c('[Ee]ntropy', '!(Intercept)')
    # ,
    # notes = c(note),
    # tex = T,
    # fontsize = 'tiny',
    # file=file.path(TABDIR, glue('reg_{endog}.tex')),
    # label = glue('tab:reg_{endog}'),
    # replace = T
    )
  )
  
  # smoothed entropy
  exog <- grep('entropy_.*_sz$', names(dt), value = T)
  print(
    etable(
      fixest::feols(.[endog] ~ sw(.[,exog]) + ..controls | sw0(user_id + ym), df),
      title = glue('{endog} on smoothed entropy'),
      order = c('[Ee]ntropy', '!(Intercept)')
      # ,
      # notes = c(note),
      # tex = T,
      # fontsize = 'tiny',
      # file=file.path(TABDIR, glue('reg_{endog}_s.tex')),
      # label = glue('tab:reg_{endog}_s'),
      # replace = T
    )
  )
}
  

