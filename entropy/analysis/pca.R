library(ISLR)

Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')
setwd('~/dev/projects/entropy/entropy/analysis')
source('helpers.R')

dt <- read_analysis_data()

cols <- grep('tag_spend_', names(dt))
d <- dt[, ..cols]

pc <- prcomp(d, scale = TRUE)

# Variance explained plots
pve <- summary(pc)$importance[2,]
xlab <- 'Principal component'
par(mfrow = c(1, 2))
plot(pve, type = 'o', ylab = 'PVE', xlab = xlab, col = 'blue')
plot(cumsum(pve), type = 'o', ylab = 'Cumulative PVE', xlab = xlab, col = 'brown3')
