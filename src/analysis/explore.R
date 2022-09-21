library(glue)
library(fixest)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')


theme_set(theme_minimal())

df <- read_debug_data()




# Entropy components --------------------------------------------------------------

components <- c("txns_count_spend", "nunique_tag_spend", "std_tag_spend")
y = "entropy_tag_spend"

for (c in components) {
  fn <- glue("scatter_entropy_{c}.png")
  g <- df %>% 
    group_by(x = .data[[c]]) %>% 
    summarise(y = mean(.data[[y]])) %>% 
    ungroup() %>% 
    filter(ntile(x, 100) < 95) %>% 
    ggplot(aes(x, y)) +
    geom_point(alpha = 0.5, colour = palette[1]) +
    labs(x = varlabs[[c]], y = varlabs[[y]]) + 
    theme(
      axis.title=element_text(size = 20),
      axis.text = element_text(size = 20),
    )
  
  ggsave(file.path(FIGDIR, fn),
         height = 2000,
         width = 3000,
         units = "px")
  print(g)
}


# Effect of smoothing -------------------------------------------------------------

legendlabs <- c(varlabs[['entropy_tag_spend']], varlabs[['entropy_tag_spend_s']])

for (c in components) {
  fn <- glue("smoothing_on_{c}.png")
  g <- df %>% 
    group_by(x = .data[[c]]) %>% 
    summarise(across(matches("entropy_tag_spend$|entropy_tag_spend_s$"), ~mean(.x))) %>%
    ungroup() %>% 
    filter(ntile(x, 100) <= 95) %>% 
    pivot_longer(!x) %>% 
    ggplot(aes(x, value, colour=name)) +
    geom_point(alpha = 0.5) +
    scale_color_hue(labels = legendlabs) +
    labs(x = varlabs[[c]], y = "Entropy", colour = "") +
    theme(
      axis.title=element_text(size = 30),
      axis.text = element_text(size = 30),
      legend.text = element_text(size = 30),
      legend.position = "top"
    )
  
  ggsave(file.path(FIGDIR, fn))
  print(g)
}


# Smoothed and unsmoothed entropy correlation -------------------------------------

df %>% 
  sample_frac(1) %>% 
  group_by(x = entropy_tag_spend) %>% 
  summarise(y = mean(entropy_tag_spend_s)) %>%
  ungroup() %>% 
  ggplot(aes(x, y)) +
  geom_point(alpha = 0.3, colour = palette[[1]]) +
  labs(x = varlabs[["entropy_tag_spend"]], y = varlabs[["entropy_tag_spend_s"]]) +
  theme(
    axis.title=element_text(size = 30),
    axis.text = element_text(size = 30)
  )
fn <- glue("smoothed_unsmoothed_corr.png")
ggsave(file.path(FIGDIR, fn))


# from here - can we make sense of this intuitively?
df %>% 
  sample_frac(0.05) %>% 
  select(x = entropy_tag, y = entropy_tag_s, nunique_tag, txns_count) %>% 
  ggplot(aes(x, y, colour = factor(txns_count))) +
  geom_point() +
  facet_wrap(~nunique_tag) +
  theme(
    legend.position = NA
  )






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
