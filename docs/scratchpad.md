# Entropy scratchpad


Strands of intestigation - papers

- Impact spend profile on savings (and other financial outcomes?) above and beyond conventional factors - also think of this as developing and understanding well one feature of the next paper.

- Predict months with zero sa inflows, using different ml models (ML
  application of data, publish in applied ml journal)

- Does entropy capture levels of stress in people's lifes?

- Classify users into types of spenders and savers using clustering analysis,
  then see whether types have different financial outcomes.




Effect of spend profile on financial outcomes

- To what extent does the way people allocate their spending determine
  financial outcomes? Allocation varies over time and across individuals. Two
  ways to assess spend allocation. Within a given period (i.e. characterise a
  single distribution - using Shannon entropy), and across time (characterise
  similarity/divergence across for each user, using Jensen-Shannon
  divergence?).

- For now, focus on the former. We find a consistent effect. But what are we
  measuring?

- We do the following:

    - Calculate different summary statistics of spend profiles

        - Unsmoothed entropy

        - Smoothed entropy

        - Grocery spend entropy

    - See whether these are related to financial outcomes


Financial outcomes (user-month level)

- Savings

    - Total/net sa inflows

    - Dummy for whether sa inflows

- Spend

    - Total spend

    - Total highly discretionary spend

- Fees

    - Total overdraft fees

    - Dummy for overdraft fees




Entropy as a measure of stress?

- Initial attempt of paper was to use entropy as a proxy of life stress
  (similar to muggleton2020evidence) and test whether it has an effect on
  savings behaviour.

- Two problems with this:

    - The way we calculate entropy significantly impacts the direction of its
    effect on savings, raising questions about what each of these different
    measures truly captures (they can't both capture stress). We are currently
    taking the view that they are one possible summary statistic of a
    user's spend profile in a given month, and are trying to understand what --
    in essence -- smoothed and unsmoothed entropy capture about these profiles.
    We might find that we don't even need entropy to represent these properties
    (e.g. we might just use the number of unique categories a person spends
    money on).

    - It is very doubtful that the number of positive spend categories truly
    reflects chaos or stress in a person's life, certainly not when there are
    only nine catgories, most of which we'd expect everyone to spend on every
    month. To the extent that spend profiles can capture chaos, I think we'd
    have to measure it based on profile consistency over time.

- Where does this leave us? What are possible paths forward?

    - Write paper based on muggleton2020evidence discussing the effect of
    smoothing, what it results from, and how this changes how we should think
    about entropy. - Smoothed seems to capture uniformity of counts, unsmoothed
    number of positive counts. Think of plausible interpretation of both of
    these (i.e. what's plausible link to savings behaviour), maybe test, and
    then wrap up.

    - Possibly in addition to above, or separately, do event studies to test
    effect of stressful life events on both entropy scores to see whether one
    of the two is related to it.

    - Calculate additional entropy scores and check whether they are related to
    above:

        - Grocery-shops based entropy (based on kantar data, remove gas
        purchases, use merchant_business_line)

        - Consistency-based entropy (Jensen-Shannon)?


- There are two dimensions here:

    - The way we calculate probabilities - e.g. what entropy score is based on (e.g. category counts, over-time consistency)

    - Whether or not we use Laplace smoothing

- All of this is, ultimately, about whether we can gain useful information from
  a person's spending profile








ML paper

- New approach: I want to make it easier for people to save. I have this entire
  dataset. Use ml to determine what predicts savings. Can we use nudges/app
  features what would help people save?

- Why don't people save?

- Lots of people think they haven't got enough savings and wish they could save
  more, yet don't. Why? What characterises those who do save?

- Given this dataset, what's the most impactful thing in terms of user's
  wellbeing that we could ask ourselves?


Entropy scores and savings behaviour relationthip

- Unsmoothed entropy increases with the number of unique categories a user
  spends money on, and is positively related to sa inflows. This means that
  users who spend money on more categories are more likely to save.

- Smoothed entropy increases in the similarity of the category counts, and is
  negatively related to sa inflows. This means that users who have more equal
  counts are less likely to save.



Thoughts on entropy calculations.

- Basket-revealed (BRV) entropy used in guidotti2015behavioural has serious
  limitations, too. An individual who purchases one particular item on each of
  their shops but apart from that purchases all different items so that each
  item appears only once across all shops would have entropy of zero (since
  that one item would be the representative basket for all shops and have
  probability 1 of occurring), even
  though their behaviour would be extremely irregular.

- Calculating a BRV measure for MDB that takes into account similarity of
  counts would be very complicated. The BRV measure akin to that used in
  guidotti2015behavioural would be to ignore counts and just focus on the
  categories with positive counts (akin to a product being bought, they ignore
  quantity bought). This doesn't make sense with LBG categories, where most
  categories have positive counts. It would make more sense with auto tags,
  where there would be more variation.


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
