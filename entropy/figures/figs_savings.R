setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(ggdist)
library(ggplot2)
library(ggthemr)
library(lubridate)
library(patchwork)
library(plyr)
library(stringr)

ggthemr('fresh')
theme_set(theme_minimal())
theme_update(
  plot.caption = element_text(hjust = 0),
  plot.tag = element_text(size = 8)
)

FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 

txns_label <- 'Number of transactions'


dt <- read_final_users_data()[is_sa_flow == T & is_debit == F]
dta <- read_analysis_data()

# dev

ggplot(dta) +
  geom_histogram(aes(sa_inflows + 1))

ggplot(dta, aes(log(month_income * 1000), log(month_spend * 1000))) +
  geom_point(shape = '.') +
  geom_smooth()



# end dev


moy <- ggplot(dt) +
  geom_bar(aes(month(date, label = T))) +
  labs(
    x = 'Month of year',
    y = txns_label
  )
moy

dom <- ggplot(dt) +
  geom_bar(aes(day(date))) +
  labs(
    x = 'Day of month',
    y = txns_label
  )
dom

d <- dt[, .N, -amount][order(-N)][1:10]
amounts <- ggplot(d) +
  geom_bar(aes(N, reorder(factor(amount), N)), stat = 'identity') +
  labs(
    x = txns_label,
    y = 'Amount'
  )
amounts


cap <- 'Notes: number of days since last transfer into savings account. Number of transactions with delay of more than 35 days are fewer than 5 percent and are not shown.'
dt <- dt[, ddate := difftime(date, shift(date), units = 'days'), user_id]
ddate <- ggplot(dt[ddate <= 35]) +
  geom_bar(aes(factor(ddate))) +
  labs(
    x = 'Days since last savings account transfer',
    y = txns_label,
    caption = cap
  )
ddate


pw <- moy + dom + amounts + ddate 
pw + plot_layout(ncol = 2)
ggsave(file.path(FIGDIR, 'savings.png'))









# Transactions by day of week ------------------------------------------------------

dt <- read_txn_data('777')

day_order <- c('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')

p <- ggplot(dt, aes(factor(weekdays(as.Date(dt$date)), level = day_order))) +
  geom_bar() +
  labs(
    x = 'Day of week',
    y = 'Number of transactions'
  ) & theme_minimal()
p

ggsave(file.path(FIGDIR, 'dow_txns.png'))



# Entropy and components -----------------------------------------------------------

dt <- read_analysis_data()

p1 <- ggplot(dt, aes(txns_count)) +
  geom_histogram(binwidth=5) +
  xlim(0, 500) +
  labs(
    x = 'Spend transactions',
    y = 'Number of observations'
  )

num_spend_cats <- dt[, rowSums(.SD > 0), .SDcols = names(dt) %like% "^spend_"]
p2 <- ggplot() +
  geom_bar(aes(x = num_spend_cats)) + 
  labs(
    x = 'Distinct spending categories',
    y = 'Number of observations'
  )

p3 <- ggplot(dt, aes(entropy_tag)) +
  geom_histogram(binwidth = .05) + 
  labs(
    x = 'Spending entropy',
    y = 'Number of observations'
  )


p1 + p2 + p3
ggsave(file.path(FIGDIR, 'entropy_hists.png'))
# look into using height and width params


