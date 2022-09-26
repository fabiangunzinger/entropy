
.PHONY: all
all: sumstats figures analysis msg


.PHONY: sumstats
sumstats:
	@printf '\n Updating sumstats table...\n'
	@Rscript src/analysis/sumstats.R


.PHONY: sampdesc 
sampdesc:
	@printf '\n Updating sample description plots...\n'
	@Rscript src/figures/sample_description.R


.PHONY: figures
figures: sampdesc


.PHONY: analysis
analysis:
	@printf '\n Updating analysis results...\n'
	@Rscript src/figures/analysis.R


.PHONY: msg
msg:
	@printf '\n Paper updated.\n'


.PHONY: data
data:
	@printf '\nProducing analysis data...\n'
	@python -m src.data.make_data


.PHONY: testdata
testdata:
	@printf '\nProducing test analysis data...\n'
	@python -m src.data.make_data --piece 0


.PHONY: test
test:
	python -m pytest --cov=entropy


