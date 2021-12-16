SHELL = /bin/sh

# RAWDIR := s3://3di-data-mdb/raw

# RAWDIR := ~/tmp
RAWDIR := s3://3di-data-mdb/raw
CLEANDIR := ~/tmp
CLEANDIR := s3://3di-project-entropy
SAMPLES := 000 777 X77 XX7
# TESTSAMPLE := 000
TESTSAMPLE := 000
FIGDATA := s3://3di-project-entropy/entropy_XX7.parquet


.PHONY: pptest
.PHONY: test
test:
	python -m pytest

pptest:
	@python -m entropy.data.make_data\
		$(RAWDIR)/mdb_$(TESTSAMPLE).parquet \
		$(CLEANDIR)/entropy_$(TESTSAMPLE).parquet


.PHONY: all
all: $(SAMPLES)


$(SAMPLES):
	@python -m entropy.data.make_data\
		$(RAWDIR)/mdb_$@.parquet\
		$(CLEANDIR)/entropy_$@.parquet

.PHONY: figures
figures:
	@python -m entropy.figures.figures $(FIGDATA)

fig_monthly_savings:
	@echo 'Producing monthly savings figure...'
	@python -m entropy.figures.monthly_savings $(FIGDATA)
