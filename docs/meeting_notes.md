

## 22 March 2022 - Tim ATI Research Software Engineering

Agenda:

- Rationale behind user > acccount > txn (is natural hierarchy, is this the
  reason?). Thought process behind creating tables. 

- How to handle generated variables and subsamples? Separate tables (and could
  they be easily updated/replaced)? Flatfiles?

- Know anyone who's got experience with hosting on AWS and knows about pricing?


Notes:

- Use ATI credits for Azure and set up a pre-configured DS vm. Then download
  MDB data to there, and use PSQL to move to db also hosted on Azure. Use Azure
  so I won't use TE resources and because Tim already works with it.

- Workflow: have minimally cleaned raw data in db, then use flat files for
  analysis data. This makes it easy to query raw data for subsets of data, and
  I can add or replace variables in analysis data by manipulating these files
  directly (e.g. to add a new variable, simply query data from sql, generate
  variable, and store in analysis data). Last example suggests the following:
  aggregators would pull required data from db instead of reading in a flat
  file. So would have to adapt this. Think about whether that's worth it and
  how easy it would be to do. Think, then start with 777 data on separate
  branch.

- Sample schema here: https://dbdiagram.io/d/62389519bed6183873cf6e2d

- Reach out ot Tim after holiday.



