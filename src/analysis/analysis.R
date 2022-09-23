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

titles <- list(
  "has_inflows" = "P(payment into savings accounts)",
  "has_investments" = "P(payment into investment funds)"
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

evars <- entropy_vars(df)

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


# Results by income quintiles -----------------------------------------------------

lab <- "inc_quint"
yvars <- c("has_inflows")
evars <- entropy_vars(df)
controls = c('month_spend', 'month_income', 'income_var')

for (y in yvars) {
  for (e in evars) {
    results <- list()
    for (q in 1:5) {
      data = df %>% filter(month_income_quint == q)
      results[[q]] <- feols(.[y] ~ sw(.[,e]) + .[controls] | ..fe, data)
    }
    print(
      etable(
        results,
        title = glue('Effect of entropy on {titles[y]} by income quintile'),
        headers=list("_Income quintile:"=list(1, 2, 3, 4, 5)),
        order = c('[Ee]ntropy', '!(Intercept)'),
        tex = T,
        fontsize = 'tiny',
        file=file.path(TABDIR, glue('reg_{y}_{e}_{lab}.tex')),
        label = glue('tab:reg_{y}_{e}_{lab}'),
        replace = T
      )
    )
  }
}  


# Results by income variability quintiles -------------------------------------------


lab <- "inc_var_quint"
yvars <- c("has_inflows")
evars <- entropy_vars(df)

for (y in yvars) {
  for (e in evars) {
    results <- list()
    for (q in 1:5) {
      data = df %>% filter(income_var_quint == q)
      results[[q]] <- feols(.[y] ~ sw(.[,e]) + ..controls | ..fe, data)
    }
    print(
      etable(
        results,
        title = glue('Effect of entropy on {titles[y]} by income variability quintile'),
        headers=list("_Income variability quintile:"=list(1, 2, 3, 4, 5)),
        order = c('[Ee]ntropy', '!(Intercept)'),
        tex = T,
        fontsize = 'tiny',
        file=file.path(TABDIR, glue('reg_{y}_{e}_{lab}.tex')),
        label = glue('tab:reg_{y}_{e}_{lab}'),
        replace = T
      )
    )
  }
}  

