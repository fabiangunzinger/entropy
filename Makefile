SHELL = /bin/sh

RAWDIR := s3://3di-data-mdb/raw
CLEANDIR := s3://3di-project-entropy
SAMPLES := 777 XX7
FIGDATA := s3://3di-project-entropy/entropy_XX7.parquet


.PHONY: pptest
.PHONY: test
test:
	python -m pytest


.PHONY: mdb_data
mdb_data: $(SAMPLES)

$(SAMPLES):
	@python -m entropy.data.make_data\
		$(RAWDIR)/mdb_$@.parquet\
		$(CLEANDIR)/entropy_$@.parquet


.PHONY: analysis analysis_data figures

analysis: analysis_data sumstats_table

analysis_data:
	@printf '\nProducing analysis data...\n'
	@python -m entropy.analysis.make_analysis_data

sumstats_table:
	@printf '\nProducing sumstats table...\n'
	@python -m entropy.analysis.sumstats_table





figures:
	@python -m entropy.figures.figures $(FIGDATA)

fig_monthly_savings:
	@echo 'Producing monthly savings figure...'
	@python -m entropy.figures.monthly_savings $(FIGDATA)

.PHONY: figures fig_user_age_hist

fig_user_age_hist:
	@python -m entropy.figures.user_age_hist $(FIGDATA)

