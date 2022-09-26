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

