library(glue)
library(fixest)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')


# Load data and add lagged entropy variables
df <- read_analysis_data() %>% 
  group_by(user_id) %>% 
  mutate(
    across(contains('entropy'), ~lag(.x, n=1), .names = "{.col}_lag"),
    has_investments = ifelse(investments > 0, 1, 0),
    dspend = dspend / 1000,
    month_income_quint = ntile(month_income, 5),
    income_var_quint = ntile(income_var, 5)
    ) %>% 
  ungroup()


setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..comps = ~txns_count_spend + nunique_tag_spend + std_tag_spend,
  ..controls = ~month_spend + month_income + has_month_income + income_var,
  ..fe = ~user_id + ym
)

yvars <- c("has_inflows")


# Main results --------------------------------------------------------------------

lab <- "main"
for (y in yvars) {
  entropy <- entropy_vars(df)
  print(
    etable(
      fixest::feols(.[y] ~ sw(.[,entropy]) + ..controls | ..fe, df),
      order = c('[Ee]ntropy', '!(Intercept)'),
      file=file.path(TABDIR, glue('reg_{y}_{lab}.tex')),
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
      order = c('[Ee]ntropy', '!Unique'),
      file=file.path(TABDIR, glue('reg_{y}_{lab}.tex')),
      replace = T
    )
  )
}


# Controlling for components ------------------------------------------------------

lab <- "comp"
evars <- c("entropy_tag_spend_z", "entropy_tag_spend_sz")
for (y in yvars) {
  results <- list()
  for (e in evars) {
    results[[e]] <- feols(.[y] ~ .[e] + sw0(..comps) + ..controls | ..fe, df)
  }
  print(
    etable(
      results[[1]], results[[2]],
      order = c('[Ee]ntropy', "Unique", "Category counts", "Number of"),
      file=file.path(TABDIR, glue('reg_{y}_{lab}.tex')),
      replace = T
    )
  )
}


# Entropy on components -----------------------------------------------------------

lab <- "comp_only"
evars <- c("entropy_tag_spend_z", "entropy_tag_spend_sz")
print(
  etable(
    feols(.[evars] ~ ..comps | sw0(..fe), df),
    order = c('!(Intercept)', "Unique", "Category counts", "Number of"),
    headers=list("Entropy (48 cats)"=2, "Entropy (48 cats, smooth)"=2),
    file=file.path(TABDIR, glue('reg_{lab}.tex')),
    replace = T
  )
)


