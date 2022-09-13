library(data.table)
library(glue)
library(fixest)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')
# source('src/analysis/fixest_settings.R')


# Load data and add lagged entropy variables
df <- read_debug_data() %>% 
  group_by(user_id) %>% 
  mutate(
    across(contains('entropy'), ~lag(.x, n=1), .names = "{.col}_lag"),
    has_investments = ifelse(investments > 0, 1, 0),
    dspend = dspend / 1000
    )
  
names(df)

setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..comps = ~mvsw(entropy_tag_spend_z, avg_spend + nunique_tag_spend + std_tag_spend),
  ..controls = c('month_spend', 'month_income', 'has_month_income', 'income_var'),
  ..fe = ~user_id + ym
)

titles <- list(
  "has_inflows" = "P(transfer into savings accounts)",
  "has_investments" = "P(transfer into investment accounts)"
)

# Main results --------------------------------------------------------------------

lab <- "main"

yvars <- c("has_inflows", "has_investments")

for (y in yvars) {
  entropy <- entropy_vars(df)
  print(
    etable(
      fixest::feols(.[y] ~ sw(.[,entropy]) + ..controls | ..fe, df),
      title = glue('Effect of entropy on {titles[y]}'),
      order = c('[Ee]ntropy', '!(Intercept)'),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{y}_{lab}.tex')),
      label = glue('tab:reg_{y}_{lab}'),
      replace = T
    )
  )
}





# Control for non-zero counts -----------------------------------------------------

lab <- "cnz"

nuniques <- list(
  "entropy_tag_z" = "nunique_tag",
  "entropy_tag_sz" = "nunique_tag",
  "entropy_tag_spend_z" = "nunique_tag_spend",
  "entropy_tag_spend_sz" = "nunique_tag_spend",
  "entropy_merchant_z" = "nunique_merchant",
  "entropy_merchant_sz" = "nunique_merchant",
  "entropy_tag_z_lag" = "nunique_tag",
  "entropy_tag_sz_lag" = "nunique_tag",
  "entropy_tag_spend_z_lag" = "nunique_tag_spend",
  "entropy_tag_spend_sz_lag" = "nunique_tag_spend",
  "entropy_merchant_z_lag" = "nunique_merchant",
  "entropy_merchant_sz_lag" = "nunique_merchant"
)

evars <- lagged_entropy_vars(df)

for (y in yvars) {
  results <- list()
  for (e in evars) {
    r <- feols(.[y] ~ .[e] + .[nuniques[e]] + ..controls | ..fe, df)
    results[[e]] <- r
  }
  print(
    etable(
      results,
      title = glue('Effect of entropy on {titles[y]}'),
      order = c('[Ee]ntropy', '!Unique'),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{y}_{lab}.tex')),
      label = glue('tab:reg_{y}_{lab}'),
      replace = T
    )
  )
}




# Lagged entropy ------------------------------------------------------------------

lab <- "lag"

for (y in yvars) {
  entropy <- lagged_entropy_vars(df)
  print(
    etable(
      fixest::feols(.[y] ~ sw(.[,entropy]) + ..controls | ..fe, df),
      title = glue('Effect of entropy on {titles[y]}'),
      order = c('[Ee]ntropy', '!Unique'),
      tex = T,
      fontsize = 'tiny',
      file=file.path(TABDIR, glue('reg_{y}_{lab}.tex')),
      label = glue('tab:reg_{y}_{lab}'),
      replace = T
    )
  )
}

