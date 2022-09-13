library(ggplot2)
library(lubridate)
library(patchwork)
library(plyr)
library(stringr)

source('helpers.R')
setwd('~/dev/projects/entropy/entropy/analysis')

theme_set(theme_minimal())
theme_update(plot.caption = element_text(hjust = 0))

FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 

dt <- read_analysis_data()

# txn counts
facet_kdes('txn_count')

# saving accounts flows
facet_kdes('^sa_.*flows$')

# tag spends
facet_kdes('spend')

# income vars
facet_kdes('income')