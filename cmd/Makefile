##
# Fluid Ontologies: Recommendation engine
#
# @file
# @version 0.1
SHELL := bash
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

.DEFAULT_GOAL := help

# alias the python- and pip-executables to the ones in the virtual environment
# py = $$(if [ -d $(CURDIR)/'.venv' ]; then echo $(CURDIR)/".venv/bin/python3"; else echo "python3"; fi)
# pip = $(py) -m pip

# Display help for targets when calling `make` or `make help`.
# To add help-tags to new targets, place them after the target-name (and
# dependencies) following a `##`. See the targets in this file for examples.
.PHONY: help
help: ## Display this help section
	@awk 'BEGIN {FS = ":.*?## "} /^[.a-zA-Z\$$/]+.*:.*?##\s/ {printf "\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

all: ## does nothing :)
	$(info nothing to be done here...)

.PHONY: kgat
kgat: ## provision the KGAT framework with custom patches
	cd $@ \
		&& tf_upgrade_v2 --intree Model/ --outtree Model_v2 --reportfile report.txt \
		&& rm -r Model \
		&& mv Model_v2 Model \
		&& cd Model \
		&& patch < ../../patches/Main.patch \
		&& patch < ../../patches/KGAT.patch \
		&& patch < ../../patches/BPRMF.patch \
		&& cd utility \
		&& patch < ../../../patches/load_data.patch

.PHONY: kgat_pytorch
kgat_pytorch: ## provision the KGAT-pytorch extension with custom patches
	cd $@/data_loader \
		&& patch < ../../patches/loader_base.patch

# end
