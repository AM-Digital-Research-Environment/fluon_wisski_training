SHELL := bash
#.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules
.DEFAULT_GOAL := help

# how many user profiles should we have for training? required profiles will be sampled
N_USERS:=100
# percentage of profiles that are modeled browsing around the KG neighborhood of random items
PERC_WITHIN_RANGE:=50
# percentage of profiles that are modeled browsing along paths in KG
PERC_ALONG_PATHS:=50
# number of interactions the profiles should have at max
N_INTERACT_MAX:=40
# and at min
N_INTERACT_MIN:=15
# and out of the max number, this many will be put into the test set
N_INTERACT_MAX_TEST:=10

# alias the python- and pip-executables to the ones in the virtual environment
py := $$(if [ -d $(CURDIR)/'.venv' ]; then echo $(CURDIR)/".venv/bin/python3"; else echo "python3"; fi)
pip = $(py) -m pip

HERE:=$(CURDIR)

ifndef DATA_NAME
	DATA_NAME:=wisski
	DATA_DIR:=$(HERE)/../datasets/$(DATA_NAME)
	USER_DATA_DIR:=$(HERE)
endif

ITEMS_FILE=$(DATA_DIR)/items_id.txt
KG_FILE=$(DATA_DIR)/kg_final.txt
ENT_FILE=$(DATA_DIR)/entities_id.txt
DIST_MAP=$(DATA_DIR)/distance_map.npy
OUT_TEST:=$(DATA_DIR)/test.txt
OUT_TRAIN:=$(DATA_DIR)/train.txt

USERS_FILE=$(USER_DATA_DIR)/user_ids.tsv
INTERACTIONS_FILE=$(USER_DATA_DIR)/user_interactions.tsv

# Display help for targets when calling `make` or `make help`.
# To add help-tags to new targets, place them after the target-name (and
# dependencies) following a `##`. See the targets in this file for examples.
.PHONY: help
help: ## Display this help section
	@awk 'BEGIN {FS = ":.*?## "} /^[.a-zA-Z\$$/]+.*:.*?##\s/ {printf "\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: all
all:
	$(info $(CURDIR))

.PHONY: clean
clean: ## run cleanup routines
	rm -f $(DIST_MAP) $(OUT_TEST) $(OUT_TRAIN)

.PHONY: trace
trace: $(HERE)/user_interactions.tsv ## run interaction tracer
	$(py) trace_interactions.py -d -v --items_file $(ITEMS_FILE) --knowledge_graph_file $(KG_FILE) --entities_file $(ENT_FILE) --interactions_file $^

.PHONY: trainingprofiles
trainingprofiles: $(OUT_TEST) $(OUT_TRAIN) ## create test and train split files

$(HERE)/user_interactions.tsv: N_USERS:=10
$(HERE)/user_interactions.tsv: PERC_WITHIN_RANGE:=50
$(HERE)/user_interactions.tsv: PERC_ALONG_PATHS:=50
$(HERE)/user_interactions.tsv: N_INTERACT_MAX:=20
$(HERE)/user_interactions.tsv: N_INTERACT_MIN:=3
$(HERE)/user_interactions.tsv: N_INTERACT_MAX_TEST:=0
$(HERE)/user_interactions.tsv: ## create a user_interactions.tsv for testing purposes
	$(py) sample_interactions.py -d --n_interact_min $(N_INTERACT_MIN) --n_interact_max $(N_INTERACT_MAX) --n_interact_test_max $(N_INTERACT_MAX_TEST) --n_profiles $(N_USERS) --perc_within_range $(PERC_WITHIN_RANGE) --perc_along_path $(PERC_ALONG_PATHS) --items_file $(ITEMS_FILE) --knowledge_graph_file $(KG_FILE) --entities_file $(ENT_FILE) --save_dir $(HERE)/

$(OUT_TEST) $(OUT_TRAIN) &: $(USERS_FILE) $(INTERACTIONS_FILE)
	$(py) sample_profiles.py -d --n_interact_min $(N_INTERACT_MIN) --n_interact_max $(N_INTERACT_MAX) --n_interact_test_max $(N_INTERACT_MAX_TEST) --n_profiles $(N_USERS) --perc_within_range $(PERC_WITHIN_RANGE) --perc_along_path $(PERC_ALONG_PATHS) --items_file $(ITEMS_FILE) --knowledge_graph_file $(KG_FILE) --entities_file $(ENT_FILE) --user_file $(USERS_FILE) --interactions_file $(INTERACTIONS_FILE) --save_dir $(DATA_DIR)

