setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

library(ggplot2)
library(patchwork)


FIGDIR = '/Users/fgu/dev/projects/entropy/output/figures' 



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


