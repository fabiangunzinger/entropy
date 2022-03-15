SHELL = /bin/sh

<<<<<<< HEAD
SAMPLES := 777 XX7
SAMPLES := X77
=======
SAMPLES := 777 X77 XX7
>>>>>>> 867f2cb86050976f404b47696737963bc4df0243
FIGDATA := s3://3di-project-entropy/entropy_XX7.parquet


.PHONY: pptest
.PHONY: test
test:
	python -m pytest --cov=entropy


.PHONY: data
data: $(SAMPLES)

$(SAMPLES):
	@printf '\nMaking sample $@...\n'
	@python -m entropy.data.make_data $@


.PHONY: rawdata
rawdata: raw_777 raw_X77 raw_XX7

raw_777:
	@printf '\nMaking sample 777...\n'
	@python -m entropy.data.make_data 777 --from-raw

raw_X77:
	@printf '\nMaking sample X77...\n'
	@python -m entropy.data.make_data X77 --from-raw

raw_XX7:
	@printf '\nMaking sample XX7...\n'
	@python -m entropy.data.make_data XX7 --from-raw


