library(fixest)
library(ggsci)
library(ggthemes)
library(ggthemr)
library(RColorBrewer)
library(scales)
library(wesanderson)


# Environment variable
Sys.setenv(AWS_PROFILE='3di', AWS_DEFAULT_REGION='eu-west-2')

# Global variables
ROOT <- '/Users/fgu/dev/projects/entropy'
FIGDIR <- file.path(ROOT, 'output/figures')
TABDIR <- file.path(ROOT, 'output/tables')
setwd(ROOT)

# Figure color scheme
palette <- pal_d3("category20c")(5) # ggsci
# palette <- brewer.pal(5, name = "Set1") # RColorBrewer
# palette <- wes_palette("IsleofDogs1") # wesanderson
# palette <- tableau_color_pal('Tableau 10')(5) # ggthemes
# palette <- ggthemr('camouflage', set_theme = FALSE)$palette$swatch # ggthemr
options(ggplot2.discrete.colour = palette)
options(ggplot2.discrete.fill = palette)

# Variable labels
varlabs <- c(
  has_inflows = "Has savings",
  sa_inflows = "Savings accounts inflows",
  sa_outflows = "Savings accounts outflows",
  sa_netflows = "Savings accounts net-inflows",

  entropy_tag_spend = "Entropy (48 cats)",
  entropy_tag_spend_s = "Entropy (48 cats, smooth)",

  entropy_tag_z = "Entropy (9 cats)",
  entropy_tag_sz = "Entropy (9 cats, smooth)",
  entropy_tag_spend_z = "Entropy (48 cats)",
  entropy_tag_spend_sz = "Entropy (48 cats, smooth)",
  entropy_merchant_z = "Entropy (merchant)",
  entropy_merchant_sz = "Entropy (merchant, smooth)",
  entropy_groc_z = "Entropy (groceries)",
  entropy_groc_sz = "Entropy (groceries, smooth)",
  
  entropy_tag_z_lag = "Entropy lag (9 cats)",
  entropy_tag_sz_lag = "Entropy lag (9 cats, smooth)",
  entropy_tag_spend_z_lag = "Entropy lag (48 cats)",
  entropy_tag_spend_sz_lag = "Entropy lag (48 cats, smooth)",
  entropy_merchant_z_lag = "Entropy lag (merchant)",
  entropy_merchant_sz_lag = "Entropy lag (merchant, smooth)",
  entropy_groc_z_lag = "Entropy lag (groceries)",
  entropy_groc_sz_lag = "Entropy lag (groceries, smooth)",
  
  prop_credit = "Paid with credit (proportion)",
  month_spend = 'Month spend',
  is_urban = 'Urban',
  is_female = 'Female',
  age = 'Age',
  year_income = "Year income",
  month_income = "Month income",
  has_regular_income = 'Has regular income',
  has_month_income = 'Has income in month',
  income_var = "Income variability",
  has_loan_repmt = 'Loan repayment',
  has_pension = 'Pension',
  has_benefits = 'Benefits',
  has_mortgage_pmt = 'Mortgage payment',
  has_rent_pmt = 'Rent payment',
  
  user_id = 'User',
  ym = 'Year-month',
  
  txns_count_spend = 'Number of spend txns (F)',
  std_tag_spend = 'Category counts std.',
  nunique_tag_spend = "Unique categories",
  nunique_tag = 'Unique categories',
  nunique_merchant = "Unique categories"
)


# fixest settings

## set fontsize of latex table produced by etable
set_font = function(x, fontsize){
  if(missing(fontsize)) return(x)
  dreamerr::check_arg_plus(fontsize, "match(tiny, scriptsize, footnotesize, small, normalsize, large, Large)")
  x[x == "%start:tab\n"] = paste0("\\begin{", fontsize, "}")
  x[x == "%end:tab\n"] = paste0("\\end{", fontsize, "}")
  return(x)
}

setFixest_etable(
  postprocess.tex = set_font,
  se.below = T,
  depvar = F,
  digits = 'r3',
  coefstat = 'confint',
  style.tex = style.tex(
    main = "base",
    tpt = TRUE,
    notes.tpt.intro = '\\footnotesize'
  )
)

setFixest_dict(varlabs)
