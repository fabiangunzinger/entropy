library(glue)
library(fixest)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')


theme_set(theme_minimal())

df <- read_debug_data()



# Effect of smoothing -------------------------------------------------------------


# Effect of smoothing on entropy scores
df %>% 
  group_by(nunique_tag_spend) %>% 
  summarise(across(matches("entropy_tag_spend$|entropy_tag_spend_s$"), ~mean(.x))) %>% 
  pivot_longer(!nunique_tag_spend) %>% 
  ggplot(aes(factor(nunique_tag_spend), value, colour=name)) +
  geom_point() +
  scale_color_hue(labels = c("Entropy", "Smoothed entropy")) +
  labs(x = "Non-zero categories", y = "(Smoothed) entropy", colour = "") +
  theme(legend.position = "top")


df %>% 
  group_by(nunique_tag_spend) %>% 
  summarise(across(matches("entropy_tag_spend_s?z$"), ~mean(.x))) %>% 
  pivot_longer(!nunique_tag_spend) %>% 
  ggplot(aes(factor(nunique_tag_spend), value, colour=name)) +
  geom_point() +
  scale_color_hue(labels = c("Smothed entropy", "Entropy")) +
  labs(x = "Non-zero categories", y = "(Smoothed) entropy", colour = "") +
  theme(legend.position = "top")



# Spending by income quintile -----------------------------------------------------


# Number of scpend categories by income quintile
df %>%
  ggplot(aes(factor(month_income_quint), nunique_tag_spend)) +
  geom_boxplot()


df %>% 
  group_by(month_income_quint) %>% 
  summarise(y = mean(nunique_tag_spend)) %>% 
  ggplot(aes(month_income_quint, y)) +
  geom_point() +
  ylim(0, 20)

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
    dspend = dspend / 1000,
    month_income_quint = ntile(month_income, 5),
    income_var_quint = ntile(income_var, 5)
  )



# Regs ----------------------------------------------------------------------------

setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..comps = ~mvsw(entropy_tag_spend_z, avg_spend + nunique_tag_spend + std_tag_spend),
  ..controls = c('month_spend', 'month_income', 'has_month_income', 'income_var'),
  ..fe = ~user_id + ym
)

titles <- list(
  "has_inflows" = "P(has savings)",
  "has_investments" = "P(has investments)"
)


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
