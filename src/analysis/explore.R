library(glue)
library(fixest)
library(latex2exp)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')

df <- read_analysis_data()

theme_set(theme_minimal())

setFixest_fml(
  ..endog = ~has_sa_inflows,
  ..comps = ~txns_count_spend + nunique_tag_spend + std_tag_spend,
  ..controls = ~month_spend + month_income + has_month_income + income_var,
  ..fe = ~user_id + ym
)




p <- "^ct_tag_(?!spend)"
d <- df %>% 
  rowwise() %>% 
  mutate(
    across(matches(p, perl = T), ~(.x + 1) / (txns_count_spend + 9), .names = "ps_{col}"),
    across(matches(p, perl = T), ~.x / txns_count_spend, .names = "p_{col}"),
    ps_std = sd(c_across(starts_with("ps_"))),
    p_std = sd(c_across(starts_with("p_"))),
  ) %>% 
  ungroup() %>% 
  mutate(
    p_std_q = ntile(p_std, 5),
    ps_std_q = ntile(ps_std, 5),
    std_tag_q = ntile(std_tag, 5),
    txns_count_spend_q = ntile(txns_count_spend, 5),
    entropy_tag_pct = ntile(entropy_tag, 100),
    entropy_tag_s_pct = ntile(entropy_tag_s, 100),
    nunique_tag_lab = paste("Unique categories:", nunique_tag)
  )






# Why does sign flip? -------------------------------------------------------------

# Some low entropy users get turned into high entropy users when smoothed
# It's because they have a lot of zero counts
# What determines whether low pos count gets turned into high entropy - the variation in probs


# facet_var <- c("ps_std_q", "txns_count_spend_q", "std_tag_q")
facet_var <- c("std_tag_q")

for (v in facet_var) {
  print(v)
  g <- d %>% 
    sample_frac(0.1) %>% 
    ggplot(aes(entropy_tag_pct, entropy_tag_s_pct, colour=factor(.data[[v]]))) + 
    geom_point(alpha = 0.7) +
    geom_smooth(method = "lm", se = FALSE, colour = "white", size=1) +
    facet_wrap(~nunique_tag_lab, nrow = 2) +
    labs(
      x = varlabs[["entropy_tag_pct"]],
      y = varlabs[["entropy_tag_s_pct"]],
      colour = unname(TeX(varlabs[[v]]))
    ) +
    theme(
      legend.position = "top"
    )
  fn <- glue("scatter_facet_{v}.pdf")
  ggsave(file.path(FIGDIR, fn), height = 2000, width = 3000, units = "px")
}


# dev tag_spend

p <- "^ct_tag_spend"
d <- df %>% 
  sample_frac(0.1) %>%
  rowwise() %>% 
  mutate(
    across(matches(p, perl = T), ~(.x + 1) / (txns_count_spend + 9), .names = "ps_{col}"),
    across(matches(p, perl = T), ~.x / txns_count_spend, .names = "p_{col}"),
    ps_std = sd(c_across(starts_with("ps_"))),
    p_std = sd(c_across(starts_with("p_"))),
  ) %>% 
  ungroup() %>% 
  mutate(
    p_std_q = ntile(p_std, 5),
    ps_std_q = ntile(ps_std, 5),
    std_tag_spend_q = ntile(std_tag_spend, 5),
    txns_count_spend_q = ntile(txns_count_spend, 5),
    entropy_tag_spend_pct = ntile(entropy_tag_spend, 100),
    entropy_tag_spend_s_pct = ntile(entropy_tag_spend_s, 100),
    nunique_tag_spend_lab = paste("Unique categories:", nunique_tag_spend)
  ) %>% 
  arrange(as.integer(nunique_tag_spend))


facet_var <- c("ps_std_q", "txns_count_spend_q", "std_tag_q")
facet_var <- c("std_tag_spend_q")

for (v in facet_var) {
  print(
    d %>% 
    ggplot(aes(entropy_tag_spend_pct, entropy_tag_spend_s_pct, colour=factor(.data[[v]]))) + 
    geom_point() +
    geom_smooth(method = "lm", se = FALSE, colour = "white", size=1) +
    facet_wrap(~nunique_tag_spend_lab) +
    labs(
      x = varlabs[["entropy_tag_pct"]],
      y = varlabs[["entropy_tag_s_pct"]],
      colour = unname(TeX(varlabs[[v]]))
    ) +
    theme(
      legend.position = "top"
    )
  # fn <- glue("scatter_facet_{v}.pdf")
  # ggsave(file.path(FIGDIR, fn), height = 2000, width = 3000, units = "px")
  )
}




# Entropy components --------------------------------------------------------------

components <- c("txns_count_spend", "nunique_tag_spend", "std_tag_spend")
y = "entropy_tag_spend"

for (c in components) {
  fn <- glue("scatter_entropy_{c}.pdf")
  g <- df %>% 
    group_by(x = .data[[c]]) %>% 
    summarise(y = mean(.data[[y]])) %>% 
    ungroup() %>% 
    filter(ntile(x, 100) < 95) %>% 
    ggplot(aes(x, y)) +
    geom_point(colour = palette[1]) +
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


# Effect of smoothing on entropy as function of component ------------------------

legendlabs <- c(varlabs[['entropy_tag_spend']], varlabs[['entropy_tag_spend_s']])

# Raw correlations
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


# Correlation after partialling out other components
plots <- list()
for (c in components) {
  
  d <- df %>% sample_frac(0.1)
  
  # Partialling out effect of other components
  b <- paste(components[components != c], collapse = "+")
  fml <- paste(c, b, sep = "~")
  model <- lm(fml, d)
  d$resid <- round(resid(model), 1)
  
  g <- d %>% 
    group_by(x = resid) %>% 
    summarise(across(matches("entropy_tag_spend$|entropy_tag_spend_s$"), ~mean(.x))) %>%
    ungroup() %>% 
    filter(between(ntile(x, 100), 5, 95)) %>% 
    pivot_longer(!x) %>% 
    ggplot(aes(x, value, colour=name)) +
    geom_point(alpha = 0.5)
  
  plots[[c]] <- g

}

plots[["txns_count_spend"]]
plots[["nunique_tag_spend"]]
plots[["std_tag_spend"]]



plot(d$std_tag_spend, d$resid)








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


# Rank differences ----------------------------------------------------------------


k <- d %>% 
  sample_frac(0.01) %>% 
  mutate(
    rdiff = abs(entropy_tag_pct - entropy_tag_s_pct),
    rdiff_q = ntile(rdiff, 5)) %>% 
  select(user_id, rdiff, rdiff_q, matches("^ct_tag_spend", perl = T))

k %>% 
  filter(rdiff_q == 1) %>% 
  sample_n(5) %>% 
  pivot_longer(matches("^ct_tag_spend", perl = T)) %>% 
  ggplot(aes(name, value)) +
  geom_bar(stat = "identity") +
  facet_wrap(~user_id, nrow = 1) +
  theme(axis.text.x = element_blank())

k %>% 
  filter(rdiff_q == 5) %>% 
  sample_n(5) %>% 
  pivot_longer(matches("^ct_tag_spend", perl = T)) %>% 
  ggplot(aes(name, value)) +
  geom_bar(stat = "identity") +
  facet_wrap(~user_id, nrow = 1) +
  theme(axis.text.x = element_blank())


kk <- k %>% 
  group_by(rdiff_q) %>% 
  summarise(across(everything(), mean))

kk %>% 
  pivot_longer(matches("^ct_tag_spend", perl = T)) %>% 
  ggplot(aes(name, value)) +
  geom_bar(stat = "identity") +
  facet_wrap(~rdiff_q, nrow = 1) +
  theme(axis.text.x = element_blank())


kk %>% summary()

kk

