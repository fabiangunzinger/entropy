library(fixest)


# set fontsize of latex table produced by etable
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
  digits = 'r3',
  coefstat = 'confint',
  style.tex = style.tex(
    main = "base",
    tpt = TRUE,
    notes.tpt.intro = '\\footnotesize'
  )
)

setFixest_dict(c(
  has_sa_inflows = "Has savings",
  sa_inflows = "Savings accounts inflows",
  sa_outflows = "Savings accounts outflows",
  sa_netflows = "Savings accounts net-inflows",
  
  entropy_tag_z = "Entropy (9 cats)",
  entropy_tag_sz = "Entropy (9 cats, smooth)",
  entropy_tag_spend_z = "Entropy (48 cats)",
  entropy_tag_spend_sz = "Entropy (48 cats, smooth)",
  entropy_merchant_z = "Entropy (merchant)",
  entropy_merchant_sz = "Entropy (merchant, smooth)",
  entropy_groc_z = "Entropy (groceries)",
  entropy_groc_sz = "Entropy (groceries, smooth)",
  
  pct_credit = "Paid with credit (%)",
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
  
  user_id = 'User id',
  ym = 'Calendar month',
  
  txns_count_spend = 'N',
  nunique_tag_spend = 'Cnz',
  std_tag_spend = 'Counts std all',
  avg_spend = 'Average spend'
))
