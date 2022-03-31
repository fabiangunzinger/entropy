library(ggdist)
library(ggplot2)
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

dt <- read_final_users_data()[tag_group == 'spend' & is_debit]


# number of user-month spend txns
data <- dt[, .N, .(user_id, ym)]
cap <- 'Notes: Kernel density estimate of number of spend\ntransactions per user-month. '
txns <- ggplot(data) +
  geom_density(aes(N)) +
  labs(
    x = num_txns, 
    y = 'Density',
    caption = cap
    )
txns

# user-month spend
data <- dt[, .(spend = sum(amount)), .(user_id, ym)][, .SD[spend < quantile(spend, .99)]]
cap <- "Notes: Kernel density estimate of user-month spend.\nTrimmed at 99th percentile."
spend <- ggplot(data) +
  geom_density(aes(spend)) +
  scale_x_continuous(labels = scales::comma) +
  labs(
    x = 'Spend (£)',
    y = 'Density',
    caption = cap
  )
spend

# number of txns per day of week
labs <- c('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
weekday <- factor(weekdays(as.Date(dt$date), abbreviate = T), level = labs)
cap <- "Notes: Spend txns per data of week. The small number of weekend and large number of Monday transactions\nreflect the fact that most banks do not post transactions on weekends."
dow <- ggplot(dt) +
  geom_bar(aes(weekday)) +
  scale_y_continuous(labels = scales::comma) +
  labs(
    x = 'Day of week',
    y = num_txns,
    caption = cap
  ) 
dow


# day of month
data <- dt[, .(txns = .N, spend = sum(amount)), .(user_id, ym, day(date))]
data <- data[, .(txns = mean(txns), spend = mean(spend)), day]
data <- data[, .(day, txns = txns / sum(txns), spend = spend / sum(spend))]
data <- melt(data, id.vars = 'day', variable.name = 'var', value.name = 'val')
data$day <- factor(data$day)
data$var <- str_to_title(data$var)
cap <- 'Notes: red dots show the proportion of the average number of transactions, blue dots the proportion of the average \namount spent on each day of the month.'
dom <- ggplot(data) +
  geom_point(aes(x = day, y = val, colour = var)) +
  scale_y_continuous(labels = scales::percent) +
  scale_colour_ggthemr_d() +
  labs(
    x = 'Day of month',
    y = prop_txns_amount,
    colour = ' ',
    caption = cap
  ) +
  theme(legend.position = c(0.9, 0.9))
dom 

# month of year
data <- dt[, .(txns = .N, spend = sum(amount)), .(user_id, ym, month(date, label = T))]
data <- data[, .(txns = mean(txns), spend = mean(spend)), month]
data <- data[, .(month, txns = txns / sum(txns), spend = spend / sum(spend))]
data <- melt(data, id.vars = 'month', variable.name = 'var', value.name = 'val')
data$month <- factor(data$month)
data$var <- str_to_title(data$var)
cap <- 'Notes: Proportion of transactions and spend by month of year.'
moy <- ggplot(data) +
  geom_point(aes(x = month, y = val, colour = var)) +
  scale_y_continuous(labels = scales::percent) +
  scale_colour_ggthemr_d() +
  labs(
    x = 'Month of year',
    y = prop_txns_amount,
    colour = '',
    caption = cap
  ) +
  theme(legend.position = c(0.95, 0.2))
moy

# txns and spend by tag
data <- dt[, .(txns = .N, spend = sum(amount)), tag]
data <- data[, .(tag, txns = txns / sum(txns), spend = spend / sum(spend))]
data <- melt(data, id.vars = 'tag', variable.name = 'var', value.name = 'val')
data$tag <- str_to_title(str_replace(data$tag, '_', ' '))
data$var <- str_to_title(data$var)
cap <- 'Number of transactions and total spend by category (9 categories).'
tags <- ggplot(data) +
  geom_point(aes(y = reorder(tag, val), x = val, colour = var)) +
  scale_x_continuous(labels = scales::label_percent(accuracy = 1L)) +
  scale_colour_ggthemr_d() +
  labs(
    x = prop_txns_amount,
    y = 'Tag',
    colour = "",
    caption = cap
  ) +
  theme(legend.position = c(0.9, 0.15))
tags

# txn spend by auto tag
data <- dt[, .(txns = .N, spend = sum(amount)), tag_auto]
data <- data[, .(tag_auto, txns = txns / sum(txns), spend = spend / sum(spend))]
data <- data[order(-rank(spend))][1:30]
data <- melt(data, id.vars = 'tag_auto', variable.name = 'var', value.name = 'val')
data$tag_auto <- str_to_title(str_replace(data$tag_auto, '_', ' '))
data$var <- str_to_title(data$var)
cap <- 'Notes: number of transactions and total spend by spend category (157 categories) for top 30 categories.'
autotags <- ggplot(data) +
  geom_point(aes(y = reorder(tag_auto, val), x = val, colour = var), size = 1) +
  scale_x_continuous(labels = scales::label_percent(accuracy = 1L)) +
  scale_colour_ggthemr_d() +
  labs(
    x = prop_txns_amount,
    y = 'Tag',
    colour = "",
    caption = cap
  ) +
  theme(legend.position = c(0.9, 0.15))
autotags

# txn spend by merchant
data <- dt[, .(txns = .N, spend = sum(amount)), merchant]
data <- data[, .(merchant, txns = txns / sum(txns), spend = spend / sum(spend))]
data <- na.omit(data)
data <- data[order(-rank(spend))][1:30]
data <- melt(data, id.vars = 'merchant', variable.name = 'var', value.name = 'val')
data$merchant <- str_to_title(data$merchant)
data$var <- str_to_title(data$var)
cap <- 'Notes: number of transactions and total spend by merchant for top 30 merchants.'
merchant <- ggplot(data) +
  geom_point(aes(y = reorder(merchant, val), x = val, colour = var), size = 1) +
  scale_x_continuous(labels = scales::label_percent(accuracy = 1L)) +
  scale_colour_ggthemr_d() +
  labs(
    x = prop_txns_amount,
    y = 'Tag',
    colour = "",
    caption = cap
  ) +
  theme(legend.position = c(0.9, 0.15))
merchant

# number of accounts used by user-month
d <- dt[, .(accounts = uniqueN(account_id)), .(user_id, ym)]
cap <- 'Notes: Number of unique account used to pay for for spend transactions by user-month.'
accounts <- ggplot(d) +
  geom_bar(aes(accounts, ..prop..)) +
  scale_y_continuous(labels = scales::percent) +
  labs(
    x = 'Unique accounts',
    y = 'User-months',
    caption = cap
  )
accounts

# txns and spend by account type
d <- dt[, .(txns = .N, spend = sum(amount)), account_type]
d <- d[, .(account_type, txns = txns / sum(txns), spend = spend / sum(spend))]
d <- melt(d, id.vars = 'account_type', variable.name = 'var', value.name = 'val')
d$var <-  str_to_title(d$var)
d$account_type <- str_to_title(d$account_type)
cap <- 'Notes: Proportion of spend transactions and total spend by account type.'
account_type <- ggplot(d) +
  geom_point(aes(y = reorder(account_type, val), x = val, colour = var)) +
  scale_colour_ggthemr_d() +
  theme(legend.position = c(.9, .2)) +
  labs(
    x = prop_txns_amount,
    y = 'Account type',
    colour = '',
    caption = cap
  )
account_type

pw <- txns + spend + dow + dom + moy + tags + autotags + merchant + accounts + account_type
pw + 
  plot_layout(ncol = 2) +
  plot_annotation(tag_levels = 'A')

ggsave(file.path(FIGDIR, 'spending.png'), width = 20, height = 30, units = 'cm')
