# 
# Code to produce sample characteristics plot
# 

library(dplyr)
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

