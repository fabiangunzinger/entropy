# 
# Code to produce sample characteristics plot
# 

library(dplyr)
library(ggplot2)

source('./src/config.R')
source('./src/helpers/helpers.R')

df <- read_analysis_data()
names(df)


# dev

base <- df %>% 
  sample_frac(0.001) %>% 
  ggplot(aes(entropy_tag, entropy_tag_s, colour = factor(nunique_tag))) +  
  geom_point()


# Set complete scheme as baseline
theme_set(theme_minimal())

# Customise elements
theme_update(
  axis.title=element_text(size = 20),
  axis.text = element_text(size = 20),
  legend.text = element_text(size = 20),
  legend.title = element_text(size = 20),
)


base +
  theme(legend.title = element_text(size = 40))

base

# dev end

lcfs <- df %>% 
  filter(ymn == 201904) %>% 
  transmute(
    yr_income = year_income * 1000,
    yr_spend = month_spend * 12 * 1000,
    source = 'MDB'
  ) %>% 
  filter(
    ntile(yr_income, 100) <= 99,
    ntile(yr_spend, 100) <= 99
    ) %>% 
  bind_rows(read_lcfs())


ntile(df$yr_spend, 100)

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
lcfs_density(lcfs, aes(yr_income, colour = source), "Disposable income (£) in 2019")
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")

fn <- "year_spend.pdf"
lcfs_density(lcfs, aes(yr_spend, colour = source), "Total spend (£) in 2019")
ggsave(file.path(FIGDIR, fn), height = 10, width = 20, units = "cm")



df %>% 
  filter(ymn == 201904) %>% 
  transmute(
    yr_spend = month_spend * 12 * 1000,
    source = 'APP'
  ) %>% 
  filter(ntile(yr_spend, 100) <= 99) %>% 
  bind_rows(lcfs_data) %>% 
  ggplot() +
  geom_density(aes(yr_spend, color = source), alpha = 0.2) +
  scale_x_continuous(labels = scales::comma) +
  labs(x = 'Total spend (£) in 2019', y = 'Density', color = "") +
  coord_cartesian(xlim = c(0, 125000)) +
  theme(
    axis.title=element_text(size = 20),
    axis.text = element_text(size = 20),
    legend.text = element_text(size = 20),
    legend.position = c(0.9, 0.9)
    )
ggsave(file.path(FIGDIR, fn), height = 2000, width = 3000, units = "px")


fn <- "age.pdf"
df %>% 
  group_by(user_id) %>% 
  summarise(age = first(age)) %>%
  count(age) %>% 
  ggplot() +
  geom_point(aes(age, n / sum(n)), colour = palette[1]) +
  scale_y_continuous(labels = scales::percent) +
  labs(x = "Age", y = "Percent") +
  theme(
    axis.title=element_text(size = 20),
    axis.text = element_text(size = 20),
    legend.text = element_text(size = 20)
    )
ggsave(file.path(FIGDIR, fn), height = 2000, width = 3000, units = "px")


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
  labs(x = 'Percent', y = 'Region') +
  theme(
    axis.title=element_text(size = 20),
    axis.text = element_text(size = 20),
    legend.text = element_text(size = 20)
    )
ggsave(file.path(FIGDIR, fn), height = 2000, width = 3000, units = "px")
