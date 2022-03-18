setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(ggplot2)
library(lubridate)
library(patchwork)


FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 
SAMPLE = 'X77'


# Savings --------------------------------------------------------------------------

dt = read_txn_data(SAMPLE)

# savings txns of users in final sample
dta = read_analysis_data(SAMPLE)
final_sample <- unique(dta$user_id)
dt <- dt[user_id %in% final_sample,]
savings <- dt[is_sa_flow == 1 & is_debit == FALSE]
setorderv(savings, c('user_id', 'date'))

# Number of days since last savings txns (remove outliers)
savings[, date_diff := difftime(date, shift(date), units = 'days'), user_id]
savings <- savings[, .SD[(date_diff < quantile(date_diff, probs = .95, na.rm = T)) & (date_diff > 1)]]
summary(savings)


txns_label <- 'Number of transactions'


g <- ggplot(savings)

p1 <- g +
  geom_bar(aes(month(date, label = T))) +
  labs(
    x = 'Month of year',
    y = txns_label
  )

p2 <- g +
  geom_bar(aes(day(date))) +
  labs(
    x = 'Day of month',
    y = txns_label
  )

amounts <- savings[, .N, -amount][order(-N)][1:10]
p3 <- ggplot(amounts) +
  geom_bar(aes(N, reorder(factor(amount), N)), stat = 'identity') +
  labs(
    x = txns_label,
    y = 'Amount'
  )

p4 <- g +
  geom_bar(aes(factor(date_diff))) +
  labs(
    x = 'Days since last savings txns',
    y = txns_label
  )


p1 + p2 + p3 + p4 + plot_layout(ncol = 2) & theme_minimal()


dd <- savings[, .(user_id, date, amount, desc, account_id, date_diff)]



# Transactions by day of week ------------------------------------------------------

dt = read_txn_data('777')

day_order <- c('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')

p <- ggplot(dt, aes(factor(weekdays(as.Date(dt$date)), level = day_order))) +
  geom_bar() +
  labs(
    x = 'Day of week',
    y = 'Number of transactions'
  ) & theme_minimal()

ggsave(file.path(FIGDIR, 'dow_txns.png'))



# Entropy and components -----------------------------------------------------------

dt = read_analysis_data()

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

p3 <- ggplot(dt, aes(entropy)) +
  geom_histogram(binwidth = .05) + 
  labs(
    x = 'Spending entropy',
    y = 'Number of observations'
  )


p1 + p2 + p3 & theme_minimal()
ggsave(file.path(FIGDIR, 'entropy_hists.png'))
# look into using height and width params


