library(latex2exp)
library(tidyverse)

source('src/config.R')
source('src/helpers/helpers.R')

df <- read_analysis_data()

theme_set(theme_minimal())


pattern <- "^ct_tag_(?!spend)"
data <- df %>% 
  sample_frac(0.1) %>% 
  rowwise() %>% 
  mutate(
    across(matches(pattern, perl = T), ~(.x + 1) / (txns_count_spend + 9), .names = "ps_{col}"),
    ps_std = sd(c_across(starts_with("ps_"))),
  ) %>% 
  ungroup() %>% 
  mutate(
    ps_std_q = ntile(ps_std, 5),
    std_tag_q = ntile(std_tag, 5),
    txns_count_spend_q = ntile(txns_count_spend, 5),
    entropy_tag_pct = ntile(entropy_tag, 100),
    entropy_tag_s_pct = ntile(entropy_tag_s, 100),
    nunique_tag_lab = paste("Unique categories:", nunique_tag)
  )

facet_var <- c("ps_std_q", "txns_count_spend_q", "std_tag_q")

for (v in facet_var) {
  g <- data %>% 
    ggplot(aes(entropy_tag_pct, entropy_tag_s_pct, colour=factor(.data[[v]]))) + 
    geom_point(alpha = 0.7) +
    geom_smooth(method = "lm", se = FALSE, colour = "white", size=1) +
    facet_wrap(~nunique_tag_lab, nrow = 2) +
    labs(
      x = varlabs[["entropy_tag_pct"]],
      y = varlabs[["entropy_tag_s_pct"]],
      colour = unname(TeX(varlabs[[v]]))
    ) +
    theme(
      legend.position = "top"
    )
  fn <- glue("scatter_facet_{v}.pdf")
  ggsave(file.path(FIGDIR, fn), height = 2000, width = 3000, units = "px")
}
