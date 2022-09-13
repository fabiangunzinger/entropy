# 
# Code to produce entropy histograms
# 

library(dplyr)
library(ggplot2)

source('src/config.R')
source('src/helpers/helpers.R')

theme_set(theme_minimal())

df <- read_debug_data()

df %>% 
  ggplot(aes(entropy_tag_spend_z)) +
  geom_density(colour = palette[1]) +
  labs(x = varlabs["entropy_tag_spend_z"], y = "Density")
