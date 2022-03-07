# Entropy scratchpad

Thoughts on entropy calculations.

- Basket-revealed (BRV) entropy used in guidotti2015behavioural has serious
  limitations, too. An individual who purchases one particular item on each of
  their shops but apart from that purchases all different items so that each
  item appears only once across all shops would have entropy of zero, even
  though their behaviour would be extremely irregular.

- Calculating a BRV measure for MDB that takes into account similarity of
  counts would be very complicated. The BRV measure akin to that used in
  guidotti2015behavioural would be to ignore counts and just focus on the
  categories with positive counts (akin to a product being bought, they ignore
  quantity bought). This doesn't make sense with LBG categories, where most
  categories have positive counts. It would make more sense with auto tags,
  where there would be more variation.


## Savings

- see nest2021supporting intro for latest figures on why short-term savings
  matter (1/4 of uk aduls can't come up with £300)

- Can think of short-term savings as saving for goal and emergency savings

- We cannot distinguish the two

- So, our focus is on short-term savings (sts)

- Is there serious research into drivers of short-term savings?



Immediate steps:

    - If there is, control for all factors found important to build model of
    what determines sts.

    - If not, build model based on reports (can, aspen, etc)

    - Check whether entropy has effect in addition
    
    - Aim of paper: determine what factors contribute to sts, and whether
    entropy is one of these factors.



Paper frame:

- Is entropy a predictor of sts?



Outcomes:

- SA outflows

- Investments 







## What do I want to do?

From the start, my main motivation for using the MDB data has been to better
understand how people save, with the ultimate idea to help them do more of it.

The current areas of work, or, really, challenges are the following:

Measuring savings: I have not yet a convincing set of savings measures. Or I
might actually have them but haven't consolidated them yet. What would be
useful is to have a section in the paper on savings, list the few different
ways in which I measure savings and why (and what types of savings I focus on)
and then show summary statistics and interesting descriptives.

Entropy: I'm not convinced that my current measure of entropy is a good one to
measure what I want to measure. I have a number of ideas for other measures. So
I could calculate them and show descriptive statistics.

How to explain savings? One possible paper is to test whether behavioural
entropy is related to savings. I think this is what I'd want to do. I don't
have another idea, and it would make for a decent second PhD paper.

Tools are in my way a bit: creating figures that go into my papers is a bit of
a pain because I build and refine the code in Jupyter and then move it to vim,
and running it takes a while.

What is really in the way?

- Ideally, I'd write all code in .py files in vim so I have everythin in one
  place. For this I need a way to send code to iPython from vim. (Truly ideal
  would be a rmd equivalent for Python which, sadly, doesn't exist.)

- Producing figures with the full data is slow the way I currently have set
  things up. I need to be able to iterate quickly as I design figures and other
  outputs. Compared to what I have now, I can achieve this by: 1) only load
  data into ram once, 2) generate figures and other outputs individually, 3)
  possibly use vm in a clever way.



## Entropy and savings

- muggleton2020evidence (ME) seem to conflate chaotic behaviour and chaotic
  environments. 

  - vernon2016predictors assesses the effect of 'household chaos' on
  development in children, where household chaos is captured by
  10 factors out of which 7 are non-behavioural factors.

  - mittal2015cognitive focus on 'childhood unpredictability', which is based
  on three factors which are only partially related to behaviours.

  - hirsh2012psychological is a theory paper.

  - frankenhuis2016cognitive is also a theory paper, and explicityly focuses on
  environmental unpredictability.





## Meaning of entropy

- The assumption of our entropy calculation is that spending on a larger set of
  mcs indicates a more chaotic lifestyle. We use user-month data, so

- The finding that higher entropy predicts higher financial distress (in
  muggleton2020evidence) says that months in which people spend money on a
  larger set of mcs are predictive of financial distress later on. We interpret
  spending on more mcs as indicative of a more chaotic lifestyle. Our
  motivating mechanism is that a more chaotic lifestyle is associated with
  impaired cognitive function, which, presumably, is associated with poor
  financial outcomes.

- Chain is: diverse spending - more chaotic lifestyle - impaired cognitive
  function - poor financial outcome.



Stressful live circumstantes > impaired cognitive functioning
(fankenhuis2016cognition) > lower self-control 
