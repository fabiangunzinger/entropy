setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(ggplot2)
library(ggthemr)
library(lubridate)
library(patchwork)
library(plyr)

ggthemr('fresh')
theme_set(theme_minimal())

FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 


dt <- read_analysis_data()

d <- dt[!duplicated(dt$user_id), .(is_female, year_income, region_name, age)]
d$is_female <- factor(d$is_female, levels = c(0, 1), labels = c('Male', 'Female'))
d$year_income <- d$year_income * 1000
d$region_name <- tools::toTitleCase(d$region_name)

base <- ggplot(d) 

income <- base +
  geom_density(aes(year_income)) +
  scale_x_continuous(labels = scales::comma) +
  labs(
    x = 'Annual income (£)',
    y = 'Density'
  )
  
age <- base + 
  geom_density(aes(age)) +
  labs(
    x = 'Age',
    y = 'Density'
  )

gender <- base +
  geom_bar(aes(x = is_female, y = (..count..) / sum(..count..))) +
  scale_y_continuous(labels = scales::percent, name = 'Percent') +
  xlab('Gender')

reorder_size <- function(x) {
  factor(x, levels = names(sort(table(x))))
}

region <- base +
  geom_point(aes(x = (..count..) / sum(..count..), y = reorder_size(`region_name`))) +
  # scale_x_continuous(labels = scales::percent) +
  labs(
    x = 'Percent',
    y = 'Region'
  )

income + age + gender + region
ggsave(file.path(FIGDIR, 'sample_desc.png'))