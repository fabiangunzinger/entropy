setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(ggplot2)
library(lubridate)
library(patchwork)
library(plyr)
library(stringr)

theme_set(theme_minimal())
theme_update(plot.caption = element_text(hjust = 0))

FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 

dt <- read_analysis_data()


facet_kdes <- function(regex, ncol = 3) {
  vars <- grep(regex, names(dt), value = T, perl = T)
  data <- melt(dt[, ..vars], measure.vars = vars)
  ggplot(data) +
    geom_density(aes(value)) +
    facet_wrap(~variable, ncol = ncol, scales = 'free')
}

# txn counts
facet_kdes('txn_count')

# saving accounts flows
facet_kdes('^sa_.*flows$')

# tag spends
facet_kdes('spend')

# income vars
facet_kdes('income')

# entropy
facet_kdes('entropy(?!.*z$)', ncol = 2)
ggsave(file.path(FIGDIR, 'entropy_kdes.png'))
