library(fixest)
library(ggplot2)


res_twfe = feols(y ~ x1 + i(time_to_treatment, ref = c(-1, -1000)) | id + year, base_stagg)

res_sa20 = feols(y ~ x1 + sunab(year_treated, year) | id + year, base_stagg)


iplot(list(res_twfe, res_sa20), sep = 0.5)

# Add the true results
att_true = tapply(base_stagg$treatment_effect_true, base_stagg$time_to_treatment, mean)[-1]
points(-9:8, att_true, pch = 15, col = 4)
legend("topleft", col = c(1, 4, 2), pch = c(20, 15, 17), 
       legend = c("TWFE", "Truth", "Sun & Abraham (2020)"))
