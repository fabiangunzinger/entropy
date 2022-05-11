library(ggplot2)
library(ggridges)
library(ggthemes)
library(hrbrthemes)
library(wesanderson)

source('helpers.R')

dt <- read_analysis_data()

ggplot(dt, aes(year_income, generation, fill = generation)) + 
  geom_density_ridges(alpha = .8, scale = 4, quantile_lines = T, quantiles = 2) + 
  scale_y_discrete(expand = c(0, 0)) +
  scale_x_continuous(expand = c(0, 0)) +
  scale_fill_manual(values = wes_palette("Zissou1"), guide = 'none') +
  labs(
    x = "Annual income (in £'000)", 
    y = "",
    caption = "Notes: Shows distribution of estimated annual income in £'000 for ) by generation. Vertical lines are medians."
  ) +
  theme_ridges(grid = T, center_axis_labels = T)
