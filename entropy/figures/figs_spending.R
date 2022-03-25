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

# select spend data
# cannot load txn data for full sample into memory, so using txns
# from users in X77 sample that are part of the analysis data
dta <- read_analysis_data()
dtt <- read_txn_data('X77')
dta_users <- unique(dta$user_id)
dtta <- dtt[user_id %in% dta_users]
dts <- dtta[tag_group == 'spend' & is_debit]
length(unique(dts$user_id))


# number of user-month spend txns
data <- dts[, .N, .(user_id, ym)]
note <- 'Note: Kernel density estimate of number of spend transactions per user-month. '
txns <- ggplot(data) +
  geom_density(aes(N)) +
  labs(
    x = 'Number of spend txns per user-month', 
    y = 'Density',
    caption = note
    )

# user-month spend
data <- dts[, .(spend = sum(amount)), .(user_id, ym)][, .SD[spend < quantile(spend, .99)]]
note <- "Note: Kernel density estimate of user-month spend. Trimmed at 99th percentile."
spend <- ggplot(data) +
  geom_density(aes(spend)) +
  scale_x_continuous(labels = scales::comma) +
  labs(
    x = 'User-month spend (£)',
    y = 'Density',
    caption = note
    )


# txns and spend by tag
data <- dts[, .(txns = .N, spend = sum(amount)), tag]
data <- data[, .(tag, txns = txns / sum(txns), spend = spend / sum(spend))]
data <- melt(data, id.vars = 'tag', variable.name = 'var', value.name = 'val')
data$tag <- str_to_title(str_replace(data$tag, '_', ' '))
data$var <- str_to_title(data$var)
note <- 'Number of transactions and total spend by spend tag.'
tags <- ggplot(data) +
  geom_point(aes(y = reorder(tag, val), x = val, colour = var), size = 3) +
  scale_x_continuous(labels = scales::label_percent(accuracy = 1L)) +
  labs(
    x = 'Percent of observations',
    y = 'Tag',
    colour = "",
    caption = note
  )


# number of txns per day of week
day_order <- c('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
dow <- factor(weekdays(as.Date(dts$date), abbreviate = T), level = day_order)
note <- "Note: Spend txns per data of week. The small number of weekend and large number of Monday transactions\nreflect the fact that most banks do not post transactions on weekends."
weekday <- ggplot(dts) +
  geom_bar(aes(dow)) +
  scale_y_continuous(labels = scales::comma) +
  labs(
    x = 'Day of week',
    y = 'Number of transactions',
    caption = note
  )

txns + spend + weekday + tags
# ggsave(file.path(FIGDIR, 'dow_txns.png'))

