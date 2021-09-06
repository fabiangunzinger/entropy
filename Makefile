SHELL = /bin/sh

RAWDIR := s3://3di-data-mdb/raw
CLEANDIR := s3://3di-project-entropy
SAMPLES := 000 777 X77
TESTSAMPLE := 000



.PHONY: test
test:
	@python -m entropy.data.make_data\
		$(RAWDIR)/mdb_$(TESTSAMPLE).parquet \
		$(CLEANDIR)/entropy_$(TESTSAMPLE).parquet

.PHONY: all
all: $(SAMPLES)


# $(SAMPLES):
# 	@python mdb/raw_parquet.py $(RAWDIR)/mdb_$@.csv $(RAWDIR)/mdb_$@.parquet
