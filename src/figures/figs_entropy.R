library(ggdist)
library(ggplot2)
library(GGally)
library(ggthemr)
library(lubridate)
library(patchwork)
library(plyr)
library(stringr)

source('helpers.R')
setwd('~/dev/projects/entropy/entropy/analysis')
ggthemr('fresh')
theme_set(theme_minimal())
theme_update(plot.caption = element_text(hjust = 0), plot.tag = element_text(size = 8))

FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 

dt <- read_final_users_data()
dta <- read_analysis_data()


# Entropy exploration --------------------------------------------------------------

# entropy kdes
facet_kdes('entropy(?!.*z$)', ncol = 2)
ggsave(file.path(FIGDIR, 'entropy_kdes.png'))


# dev
dta[, entq := cut(entropy_tag_auto, quantile(entropy_tag_auto, probs = 0:5/5), include.lowest = T, labels = F)]

vars <- grep('user|ym|spend|entq', names(dta), value = T)
d <- melt(dta[, ..vars], id.vars = c('user_id', 'ym', 'entq'))
d

ggplot(d, aes(x = factor(entq), value)) +
  geom_boxplot() +
  facet_wrap(~variable, ncol = 3, scales = 'free')
  
