SHELL = /bin/sh

SAMPLES := 777 XX7
FIGDATA := s3://3di-project-entropy/entropy_XX7.parquet


.PHONY: pptest
.PHONY: test
test:
	python -m pytest


.PHONY: data
data: $(SAMPLES)

$(SAMPLES):
	@printf '\nMaking sample $@...\n'
	@python -m entropy.data.make_data $@


.PHONY: analysis figures

analysis: analysis_data sumstats_table

sumstats_table:
	@printf '\nProducing sumstats table...\n'
	@python -m entropy.analysis.sumstats_table

.PHONY: figures
figures:
	@python -m entropy.figures.figures $(FIGDATA)

