library(data.table)
library(glue)
library(fixest)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')
source('src/analysis/fixest_settings.R')


# Load data and add lagged entropy variables
df <- read_analysis_data("XX0") %>% 
  group_by(user_id) %>% 
  mutate(
    across(contains('entropy'), ~lag(.x, n=1), .names = "{.col}_lag"),
    has_investments = ifelse(investments > 0, 1, 0)
    ) 
  mutate() %>% 
  

names(df)

setFixest_fml(
  ..endog = ~has_sa_inflows,
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



yvars <- c("has_inflows", "inflows", "has_investments", "investments", "dspend")



# Main results --------------------------------------------------------------------

entropy_vars <- function(df) {
  entropy_z <- grep('^entropy_(tag|merchant).*_z$', names(df), value = T)
  entropy_sz <- grep('^entropy_(tag|merchant).*_sz$', names(df), value = T)
  c(entropy_z, entropy_sz)
}

for (y in yvars) {
  entropy <- entropy_vars(df)
  print(
    etable(
      fixest::feols(.[y] ~ sw(.[,entropy]) + ..controls | user_id + ym, df),
      title = glue('Effect of entropy on {y}'),
      order = c('[Ee]ntropy', '!(Intercept)'),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{y}.tex')),
      label = glue('tab:reg_{y}'),
      replace = T
    )
  )
}




# Lagged entropy ------------------------------------------------------------------


sort(grep('entropy_(tag|merchant).*_z', names(df), value = T))


for (y in yvars) {
  
  # Unsmoothed entropy
  entropy <- sort(grep('entropy_(tag|merchant).*_z', names(df), value = T))
  print(
    etable(
      fixest::feols(.[y] ~ sw(.[,entropy]) + ..controls | user_id + ym, df),
      title = glue('Effect of lagged entropy on {y}'),
      order = c('[Ee]ntropy'),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{y}_lagged_z.tex')),
      label = glue('tab:reg_{y}_lagged_z'),
      replace = T
    )
  )
  
  # Smoothed entropy
  entropy <- sort(grep('entropy_(tag|merchant).*_sz', names(df), value = T))
  print(
    etable(
      fixest::feols(.[y] ~ sw(.[,entropy]) + ..controls | user_id + ym, df),
      title = glue('Effect of lagged entropy on {y}'),
      order = c('[Ee]ntropy'),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{y}_lagged_sz.tex')),
      label = glue('tab:reg_{y}_lagged_sz'),
      replace = T
    )
  )
}




# Control for non-zero counts -----------------------------------------------------


# nuniques <- list(
#   "entropy_tag_z" = "nunique_tag",
#   "entropy_tag_sz" = "nunique_tag",
#   "entropy_tag_spend_z" = "nunique_tag_spend",
#   "entropy_tag_spend_sz" = "nunique_tag_spend",  
#   "entropy_merchant_z" = "nunique_merchant",
#   "entropy_merchant_sz" = "nunique_merchant"
# )
# 
# yvars <- c("has_inflows")
# 
# entropy_vars <- grep('entropy_(tag|merchant).*(s)?z$', names(df), value = T)
# 
# 
# for (y in yvars) {
#   for (e in entropy_vars) {
#     print(
#       etable(
#         feols(.[y] ~ .[e] + ..controls | user_id + ym, df),
#         feols(.[y] ~ .[e] + .[nuniques[e]] + ..controls | user_id + ym, df),
#         feols(.[y] ~ .[e] + ..controls | user_id + ym, df),
#         feols(.[y] ~ .[e] + .[nuniques[e]] + ..controls | user_id + ym, df),
#         title = glue('Effect of entropy on {y}'),
#         order = c('[Ee]ntropy', '!(Intercept)')
#         # ,
#         # tex = T,
#         # fontsize = 'tiny',
#         # file=file.path(TABDIR, glue('reg_{y}.tex')),
#         # label = glue('tab:reg_{y}'),
#         # replace = T
#       )
#     )    
#   }
# }
