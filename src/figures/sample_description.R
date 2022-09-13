# 
# Code to produce sample characteristics plot
# 

library(cowplot)
library(dplyr)
library(ggplot2)
library(lubridate)
library(patchwork)

source('./src/config.R')
source('./src/helpers/helpers.R')

theme_set(theme_minimal())

df <- read_debug_data()


app_lcfs_data <- df %>% 
  filter(ymn == 201904) %>% 
  transmute(
    yr_income = month_income * 12,
    yr_spend = month_spend * 12,
    source = 'APP'
  ) %>% 
  bind_rows(read_lcfs())


year_income <- app_lcfs_data %>%
  ggplot() +
  geom_density(aes(yr_income, color = source), alpha = 0.2) +
  scale_x_continuous(labels = scales::comma) +
  labs(x = 'Disposable income (£) in 2019', y = 'Density', color = "") +
  theme(legend.position = c(0.9, 0.9))


year_spend <- app_lcfs_data %>% 
  ggplot() +
  geom_density(aes(yr_spend, color = source), alpha = 0.2) +
  scale_x_continuous(labels = scales::comma) +
  labs(x = 'Total spend (£) in 2019', y = 'Density', color = "") +
  coord_cartesian(xlim = c(0, 125000)) +
  theme(legend.position = c(0.9, 0.9))


age <- df %>% 
  group_by(user_id) %>% 
  summarise(age = first(age)) %>%
  count(age) %>% 
  ggplot() +
  geom_point(aes(age, n / sum(n)), colour = palette[1]) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = "Age", y = "Percent")


gender <- df %>%
  group_by(user_id) %>%
  summarise(gender = first(is_female)) %>%
  mutate(gender = factor(gender, labels = c("Male", "Female"))) %>% 
  count(gender) %>% 
  mutate(prop = n / sum(n)) %>% 
  ggplot() +
  geom_bar(aes(gender, prop), stat = "identity", fill = palette[1]) +
  scale_y_continuous(labels = scales::percent) +
  theme(legend.position = "none") +
  labs(x = "", y = "Percent")


region <- df %>%
  group_by(user_id) %>% 
  summarise(region = first(region)) %>% 
  count(region) %>%
  mutate(region = tools::toTitleCase(region), prop = n / sum(n)) %>% 
  ggplot() +
  geom_bar(aes(y = reorder(region, prop), x = prop), 
           stat = "identity",  fill =  palette[1]) +
  scale_x_continuous(labels = scales::percent) +
  theme(legend.position = "none") +
  labs(x = 'Percent', y = 'Region')


active_accounts <- df %>%
  group_by(user_id) %>% 
  summarise(accounts_active = first(accounts_active)) %>% 
  count(accounts_active) %>% 
  mutate(prop = n / sum(n)) %>% 
  ggplot() +
  geom_bar(aes(factor(accounts_active), prop), stat = "identity", fill = palette[1]) +
  labs(x = "Number of active accounts (by user-month)", y = "Count")


plot_grid(
  year_income, year_spend, age, gender, region, active_accounts,
  labels = "AUTO",
  ncol = 2
)

figname <- 'sample_description.png'
ggsave(
  file.path(FIGDIR, figname),
  height = 2000,
  width = 3000,
  units = "px"
)



