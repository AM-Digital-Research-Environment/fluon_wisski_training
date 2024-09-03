SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
.DEFAULT_GOAL := help

# alias the python- and pip-executables to the ones in the virtual environment
py := $$(if [ -d $(CURDIR)/'.venv' ]; then echo $(CURDIR)/".venv/bin/python3"; else echo "python3"; fi)
pip = $(py) -m pip

TRAINED_CLUSTER:=$(CLUSTER_OUTPUT_DIR)/clustering.joblib
TRAINED_CLUSTER_DATA:=$(CLUSTER_OUTPUT_DIR)/clustering_data.npy
TRAINED_CLUSTER_STATS:=$(CLUSTER_OUTPUT_DIR)/cluster_stats.joblib
TRAINED_CLUSTER_PLOTDIR:=$(CLUSTER_OUTPUT_DIR)/plots/
TRAINED_CLUSTER_OUTPUT:=$(CLUSTER_OUTPUT_DIR)/cluster.csv
TRAINED_MODEL_OUTPUT:=$(CLUSTER_OUTPUT_DIR)/recommendations.csv

# Display help for targets when calling `make` or `make help`.
# To add help-tags to new targets, place them after the target-name (and
# dependencies) following a `##`. See the targets in this file for examples.
.PHONY: help
help: ## Display this help section
	@awk 'BEGIN {FS = ":.*?## "} /^[.a-zA-Z\$$/]+.*:.*?##\s/ {printf "\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: training
training: $(TRAINED_CLUSTER_OUTPUT) $(TRAINED_MODEL_OUTPUT) ## cluster data and derive recommendations
	$(info $(CURDIR))

.PHONY: publish
publish: $(TRAINED_CLUSTER_STATS) $(TRAINED_CLUSTER_PLOTDIR)
	mkdir -p $(FINAL_OUTPUT_DIR) && cp -r $^ $(FINAL_OUTPUT_DIR)

$(TRAINED_CLUSTER): $(LATEST_PTH) 
	mkdir -p $(CLUSTER_OUTPUT_DIR) \
		&& $(py) cluster_training.py \
		--data_name $(DATA_NAME) \
		--data_dir $(DATA_DIR) \
		--Ks '[$(K)]' \
		--pretrain_model_path $(LATEST_PTH)

$(TRAINED_CLUSTER_DATA) $(TRAINED_CLUSTER_STATS) $(TRAINED_CLUSTER_OUTPUT) $(TRAINED_CLUSTER_PLOTDIR) &: $(TRAINED_CLUSTER)
	$(py) cluster_inspection.py \
		--cluster $(TRAINED_CLUSTER) \
		--data $(TRAINED_CLUSTER_DATA) \
		--stats $(TRAINED_CLUSTER_STATS) \
		--plotdir $(TRAINED_CLUSTER_PLOTDIR) \
		--outfile $(TRAINED_CLUSTER_OUTPUT)

$(TRAINED_MODEL_OUTPUT): $(LATEST_PTH)
	$(py) cluster_recommender.py \
		--data_name $(DATA_NAME) \
		--data_dir $(DATA_DIR) \
		--Ks '[$(K)]' \
		--pretrain_model_path $(LATEST_PTH)
