# 
# Code to produce entropy histograms
# 

library(dplyr)
library(ggplot2)
library(tidyverse)
library(tidytext)

source('src/config.R')
source('src/helpers/helpers.R')

theme_set(theme_minimal())

df <- read_debug_data()

# Entropy hist
df %>% 
  ggplot(aes(entropy_tag_spend_z)) +
  geom_density(colour = palette[1]) +
  labs(x = varlabs["entropy_tag_spend_z"], y = "Density")


# Spend profile of min and max entropy cases
df %>% 
  filter(spend_cash < 0.05 * month_spend,
         entropy_tag_spend > 0) %>% 
  arrange(entropy_tag_spend) %>% 
  slice(-(4:(n() - 3))) %>% 
  mutate(userymn = user_id * 1e6 + ymn) %>% 
  select(userymn, entropy_tag_spend, matches("^count_")) %>%
  pivot_longer(cols = matches("^count_")) %>% 
  ggplot() +
  geom_point(aes(reorder_within(name, -value, userymn), value)) +
  facet_wrap(~userymn)


df %>% 
  filter(entropy_tag_spend == 0) %>% 
  select(entropy_tag_spend, matches("^count_")) %>%
  pivot_longer(!entropy_tag_spend) %>% 
  filter(value > 0) %>% 
  group_by(name) %>% 
  count()
