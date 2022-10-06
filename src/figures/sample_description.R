# 
# Code to produce sample characteristics plot
# 

library(tidyverse)
library(ggplot2)

source('./src/config.R')
source('./src/helpers/helpers.R')

# Set complete scheme as baseline
theme_set(theme_minimal())

# Customise elements
theme_update(
  axis.title=element_text(size = 14),
  axis.text = element_text(size = 14),
  legend.text = element_text(size = 14),
  legend.title = element_text(size = 14),
)


df <- read_analysis_data()



lcfs_data <- df %>% 
  filter(ymn == 201904) %>% 
  transmute(
    yr_income = year_income * 1000,
    yr_spend = month_spend * 12 * 1000,
    source = 'MDB'
  ) %>% 
  bind_rows(read_lcfs()) %>% 
  filter(
    ntile(yr_spend, 100) <= 99,
    ntile(yr_income, 100) <= 99
    ) %>% 
  mutate(source = factor(source, levels = c("MDB", "LCFS")))


lcfs_density <- function(data, mapping, xlabel) {
  ggplot(data, mapping) +
    geom_density() +
    scale_x_continuous(labels = scales::comma) +
    labs(x = xlabel, y = 'Density') +
    theme(
      legend.position = c(0.9, 0.9),
      legend.title = element_blank()
    )
}


fn <- "year_income.pdf"
lcfs_density(
  lcfs_data,
  mapping = aes(yr_income, colour = source),
  xlabel = "Disposable income (£) in 2019"
  )
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")


fn <- "year_spend.pdf"
lcfs_density(
  lcfs_data,
  mapping = aes(yr_spend, colour = source),
  xlabel = "Total spend (£) in 2019"
  )
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")


fn <- "age.pdf"
df %>% 
  group_by(user_id) %>% 
  summarise(age = first(age)) %>%
  count(age) %>% 
  ggplot() +
  geom_point(aes(age, n / sum(n)), colour = palette[1]) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = "Age", y = "Percent")
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")


fn <- "region.pdf"
df %>%
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
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")


entropy_density <- function(data, varname) {
  data %>% 
    select(matches(glue("^{varname}(_s)?$"))) %>%
    pivot_longer(everything()) %>% 
    rowwise() %>% 
    mutate(name = factor(varlabs[[name]])) %>%
    ungroup() %>%  
    ggplot(aes(value, colour = name)) +
    geom_density() +
    labs(y = "Density", x = "Entropy") +
    theme(
      legend.title = element_blank(),
      # legend.position = "top"
      legend.position = c(0.175, 0.9),
    )
}

varname <- "entropy_tag"
fn <- glue("{varname}.pdf")
entropy_density(df, varname)
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")

varname <- "entropy_tag_spend"
fn <- glue("{varname}.pdf")
entropy_density(df, varname)
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")


taglabs <- c(
  tag_communication = "Communication",
  tag_finance = "Finance",
  tag_hobbies = "Hobbies",
  tag_household = "Household",
  tag_motor = "Motor",
  tag_other_spend = "Other spend",
  tag_retail = "Retail",
  tag_services = "Services",
  tag_travel = "Travel",
  tag_spend_groceries = "Groceries",
  tag_spend_housing = "Housing",
  tag_spend_household = "Household",
  tag_spend_vehicle = "Vehicle",
  tag_spend_loan.repayment = "Loan repayment",
  tag_spend_eating.out = "Eating out",
  tag_spend_energy.and.water = "Energy and water",
  tag_spend_clothes.and.shoes = "Clothing",
  tag_spend_taxes = "Taxes",
  tag_spend_entertainment..tv..media = "Entertainment",
  tag_spend_insurance = "Insurance",
  tag_spend_home = "Home",
  tag_spend_phone.and.mobile = "Phone",
  tag_spend_public.transport = "Public transport",
  tag_spend_holidays = "Holidays"
)

spendlabs <- list(
  tag = "Spending category (9)",
  tag_spend = "Spending category (48)"
)

spend_breakdown <- function(data, varname) {
  data %>% 
    sample_frac(0.001) %>% 
    select(matches(glue("^(ct|sp)_{varname}(?!_spend)(?!_cash)"), perl = T)) %>% 
    rowwise() %>%
    mutate(
      across(starts_with("sp"), ~.x / sum(c_across(starts_with("sp_")))),
      across(starts_with("ct"), ~.x / sum(c_across(starts_with("ct_"))))
    ) %>% 
    ungroup() %>% 
    summarise(across(everything(), mean)) %>% 
    pivot_longer(everything()) %>% 
    extract(name, c("metric", "name"), "(sp|ct)_(.*)") %>% 
    pivot_wider(names_from = metric, values_from = value) %>% 
    arrange(desc(sp)) %>% 
    head(15) %>% 
    pivot_longer(!name, names_to = "metric", values_to = "value") %>% 
    rowwise() %>%
    mutate(name = factor(taglabs[[name]])) %>%
    ggplot(aes(value, reorder(name, desc(name)), colour = metric)) +
    geom_point() +
    scale_colour_discrete(breaks=c("ct", "sp"), labels=c("Txns", "Spend")) +
    scale_x_continuous(labels = scales::percent) +
    labs(
      x = "Percentage of monthly spend/number of txns",
      y = spendlabs[[varname]]
    ) +
    theme(legend.title = element_blank(), legend.position = c(0.9, 0.1))
}

varname <- "tag"
fn <- glue("breakdown_{varname}.pdf")
spend_breakdown(df, varname)
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")

varname <- "tag_spend"
fn <- glue("breakdown_{varname}.pdf")
spend_breakdown(df, varname)
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")



spend_profile <- function(data, varname) {
  data %>% 
    mutate(q = factor(ntile(.data[[glue("entropy_{varname}")]], 5))) %>%
    select(q, matches(glue("^ct_{varname}_(?!spend)"), perl = T)) %>% 
    group_by(q) %>% 
    summarise(across(everything(), mean)) %>% 
    filter(q %in% c(1, 3, 5)) %>% 
    pivot_longer(!q) %>% 
    ggplot(aes(reorder(name, desc(value)), value, fill = q)) +
    geom_bar(stat = "identity", position = "dodge") +
    labs(
      x = spendlabs[[varname]],
      y = "Number of transactions",
      fill = "Entropy\nquintile\n(mean)"
      ) +
    theme(
      axis.text.x = element_blank(),
      legend.position = c(0.9, 0.8)
      )
}

varname <- "tag_spend"
fn <- glue("spend_profile_{varname}.pdf")
spend_profile(df, varname)
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")

varname <- "tag"
fn <- glue("spend_profile_{varname}.pdf")
spend_profile(df, varname)
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")
