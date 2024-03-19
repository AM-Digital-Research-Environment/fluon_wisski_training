SHELL := bash
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# dataset to be used. must have a folder in datasets/
DATA_NAME:=wisski
#FORCE:=force
# set to 'force' to force rebuild by fetching user and interaction data
FORCE:='no'
# can be adjusted to KGAT or CKE
ALGO:=KGAT

# config paths
HERE:=${CURDIR}
REMOTE_BASE_DIR:=$(HERE)
SAVE_DIR:=trained_model/$(ALGO)/$(DATA_NAME)
PUB_DEST:=/path/to/destination/
PUB_HOST:=http://127.0.0.1:5000
PUB_ENDPOINT_USER:=dmkg
#~ NOSYNC:=$(HERE)/403.23.99__tmp
#NOSYNC_DATADIR_NEL:=$(NOSYNC)/nel

# create a Makefile.local to override these last settings
-include Makefile.local
ifndef PUB_ENDPOINT_PASSWD
$(error please set PUB_ENDPOINT_PASSWD)
endif
# remaining settings should be host-independent

# more publication-related settings
PUB_COMMAND:=cp
PUB_ENDPOINT_TRIGGER_UPDATE:=/maintenance/v1/db/update

ifdef INIT
$(info assuming ice-cold start. building everything from scratch)
endif

ifdef $(NOSYNC)
RSYNC_SETTINGS:=-av --delete --exclude $(shell basename $(NOSYNC)) --exclude *docker-compose.yml --exclude .git
else
RSYNC_SETTINGS:=-av --delete --no-links
endif

ifeq ($(ALGO),KGAT)
ALGO_PYTHON_SCRIPT_PYT:=main_kgat.py
ALGO_PYTHON_PARAM_MODELTYPE:=kgat
ALGO_PYTHON_PARAM_ALGTYPE:=kgat
ALGO_PARAMS:=--alg_type $(ALGO_PYTHON_PARAM_ALGTYPE) --dataset $(DATA_NAME) --regs [1e-5,1e-5] --layer_size [64,32,16] --embed_size 64 --lr 0.0001 --epoch 1000 --verbose 50  --batch_size 1024 --node_dropout [0.1] --mess_dropout [0.1,0.1,0.1] --use_att True --use_kge True
ALGO_PTH_DIR:=$(HERE)/kgat_pytorch/trained_model/$(ALGO)/$(DATA_NAME)/embed-dim64_relation-dim64_random-walk_bi-interaction_64-32-16_lr0.0001_pretrain1
else ifeq ($(ALGO),CKE)
ALGO_PYTHON_SCRIPT_PYT:=main_cke.py
ALGO_PYTHON_PARAM_MODELTYPE:=cke
ALGO_PYTHON_PARAM_ALGTYPE:=bi
$(error need to adjust some more settings using CKE)
endif

ifneq ("$(wildcard $(ALGO_PTH_DIR)/*.pth)","")
	LATEST_PTH:=$(shell find $(ALGO_PTH_DIR) -newer kgat_pytorch -name '*.pth' -exec stat -c '%Y %n' {} \; | sort -nr | head -n 1 | cut -f2 -d' ')
else
	LATEST_PTH:=$(ALGO_PTH_DIR)/*.pth
endif

CLUSTER_OUTPUT_DIR:=$(HERE)/recommendations/trained_model/$(ALGO)/$(DATA_NAME)/
TRAINED_CLUSTER_OUTPUT:=$(CLUSTER_OUTPUT_DIR)/cluster.csv
TRAINED_MODEL_OUTPUT:=$(CLUSTER_OUTPUT_DIR)/recommendations.csv
FINAL_OUTPUT_DIR:=$(HERE)/pub/$(DATA_NAME)/
FINAL_MODEL_OUTPUT:=$(FINAL_OUTPUT_DIR)/recommendations.csv
FINAL_CLUSTER_OUTPUT:=$(FINAL_OUTPUT_DIR)/cluster.csv
USER_DATA_DIR:=$(HERE)/datasets/fluon_refsrv
USERS_FILE=$(USER_DATA_DIR)/user_ids.tsv
ITEMS_FILE=$(HERE)/datasets/$(DATA_NAME)/items_id.txt
INTERACTIONS_FILE=$(USER_DATA_DIR)/user_interactions.tsv

Ks:=20, 40, 60, 80, 100
KG_ITEMS_FILE:=$(HERE)/datasets/$(DATA_NAME)/items_id.txt
KG_ITEMS_N:=$(shell cut -f2 $(KG_ITEMS_FILE) | sort -nrk1,1 | head -1 | awk '{print $$1 + 1}') # increment result by one as numbering starts at 0

#~ .INTERMEDIATE: $(DIRNE)/config.py

.DEFAULT_GOAL := help

# alias the python- and pip-executables to the ones in the virtual environment
py = $$(if [ -d $(CURDIR)/'.venv' ]; then echo $(CURDIR)/".venv/bin/python3"; else echo "python3"; fi)
pip = $(py) -m pip

# Display help for targets when calling `make` or `make help`.
# To add help-tags to new targets, place them after the target-name (and
# dependencies) following a `##`. See the targets in this file for examples.
.PHONY: help
help: ## Display this help section
	@awk 'BEGIN {FS = ":.*?## "} /^[.a-zA-Z\$$/]+.*:.*?##\s/ {printf "\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

all: ## does nothing :) 
	$(info nothing to be done here...)

ifdef REMOTE
.PHONY: clean output training sync_here sync_to_remote test
training output: sync_to_remote
	ssh -t -x -a $(REMOTE) '(screen -S bla bash -c "make -C $(REMOTE_BASE_DIR) $@ ; exec bash")'
test:  sync_to_remote
	ssh $(REMOTE) make -C $(REMOTE_BASE_DIR) $@
clean:
	ssh $(REMOTE) make -C $(REMOTE_BASE_DIR) $@
sync_to_remote:
	ssh $(REMOTE) "mkdir -p $(REMOTE_BASE_DIR)" && rsync $(RSYNC_SETTINGS) $(HERE)/ $(REMOTE):$(REMOTE_BASE_DIR)
sync_here:
	scp $(REMOTE):$(REMOTE_BASE_DIR)/changelist changelist && rsync $(RSYNC_SETTINGS) --files-from=changelist $(REMOTE):$(REMOTE_BASE_DIR) $(HERE) && rm -f changelist && ssh $(REMOTE) "rm -f $(REMOTE_BASE_DIR)/changelist"
# ssh -o LogLevel=QUIET -t -x -a $(REMOTE) '[ -f $(REMOTE_BASE_DIR)/changelist ] && echo "exist" || echo "absent"'

else
.PHONY: clean output init
init: clean $(USERS_FILE) $(INTERACTIONS_FILE) datasets/wisski/kg_final.txt datasets/wisski/train.txt ## re-initialization of training. attention, deletes previous training outputs!
	$(info initialized. sure you ran everything with INIT=1 as environment variable?)

.PHONY: find_ref
find_ref:
	rm -f find_ref && touch find_ref

changelist:
	$(shell find . ! -path . -newermm find_ref -print > changelist && rm -f find_ref)

.PHONY: output
output: find_ref $(FINAL_MODEL_OUTPUT) $(FINAL_CLUSTER_OUTPUT) changelist ## create output files from training
	$(info done)

.PHONY: training
training: find_ref $(TRAINED_MODEL_OUTPUT) changelist ## do just the training
	$(info done)

.PHONY: publish
publish: $(FINAL_CLUSTER_OUTPUT) $(FINAL_MODEL_OUTPUT) ## publish results to fluon_refsrv
	$(PUB_COMMAND) $(HERE)/datasets/$(DATA_NAME)/items_id.txt $(PUB_DEST)/items_id.txt && \
	$(MAKE) -C proc_clustering publish PUB_COMMAND=$(PUB_COMMAND) PUB_DEST="$(PUB_DEST)" && \
	curl -X POST -H 'accept: application/json' --user $(PUB_ENDPOINT_USER):$(PUB_ENDPOINT_PASSWD) $(PUB_HOST)$(PUB_ENDPOINT_TRIGGER_UPDATE) | grep -v true  && echo "success" || echo "failure in update"

.PHONY: clean
clean: ## Cleanup routines. Covers training outputs as well!
	rm -f $(FINAL_CLUSTER_OUTPUT) $(FINAL_MODEL_OUTPUT)
	rm -f -r $(CLUSTER_OUTPUT_DIR)
	rm -f -r $(FINAL_OUTPUT_DIR)
	rm -f -r kgat/Model/pretrain/$(DATA_NAME)
	rm -f -r kgat/Model/weights/$(DATA_NAME)
	rm -f -r kgat_pytorch/datasets/pretrain/$(DATA_NAME)
	rm -f -r kgat_pytorch/trained_model/$(ALGO)/$(DATA_NAME)

kgat:
	git submodule add https://github.com/xiangwang1223/knowledge_graph_attention_network.git $@ && \
	cd $@ && \
	tf_upgrade_v2 --intree Model/ --outtree Model_v2 --reportfile report.txt && \
	rm -r Model && mv Model_v2 Model && cd Model && \
	patch < ../../patches/Main.patch && \
	patch < ../../patches/KGAT.patch && \
	patch < ../../patches/BPRMF.patch && \
	cd utility && \
	patch < ../../../patches/load_data.patch

kgat_pytorch:
	git submodule add https://github.com/LunaBlack/KGAT-pytorch.git $@ && cd $@/data_loader && patch < ../../patches/loader_base.patch

datasets/wisski/train.txt datasets/wisski/test.txt &: $(USERS_FILE) $(INTERACTIONS_FILE)
	$(MAKE) -C proc_fo trainingprofiles DATA_NAME="$(DATA_NAME)" USER_DATA_DIR="$(USER_DATA_DIR)" DATA_DIR="$(HERE)/datasets/$(DATA_NAME)/"

datasets/wisski/kg_final.txt:
	cd datasets/wisski && make kg

kgat/Model/pretrain/$(DATA_NAME)/mf.npz: kgat datasets/$(DATA_NAME)/kg_final.txt datasets/$(DATA_NAME)/train.txt datasets/$(DATA_NAME)/test.txt
	cd kgat && ( [ -d Data/$(DATA_NAME) ] || ln -s $(HERE)/datasets/$(DATA_NAME) Data/$(DATA_NAME) ) && cd Model && \
	$(py) Main.py $(ALGO_PARAMS) --model_type bprmf --save_flag 1 --pretrain -1 --report 0 && $(py) Main.py $(ALGO_PARAMS) --model_type bprmf --save_flag -1 --pretrain 1 --report 0

kgat_pytorch/datasets/pretrain/$(DATA_NAME)/mf.npz: kgat_pytorch kgat/Model/pretrain/$(DATA_NAME)/mf.npz
	[ -f $@ ] || ( mkdir -p kgat_pytorch/datasets/pretrain/$(DATA_NAME) && ln -s $(HERE)/kgat/Model/pretrain/$(DATA_NAME)/mf.npz $@ )

train_kgat: kgat/Model/pretrain/$(DATA_NAME)/mf.npz
	cd kgat/Model && $(py) Main.py $(ALGO_PARAMS) --model_type $(ALGO_PYTHON_PARAM_MODELTYPE) --pretrain -1 --save_flag 1 --report 0

train_kgat_pytorch: kgat_pytorch/datasets/pretrain/$(DATA_NAME)/mf.npz
	cd kgat_pytorch && $(py) $(ALGO_PYTHON_SCRIPT_PYT) --use_pretrain 1 --evaluate_every 10 --Ks '[$(Ks)]' --data_name $(DATA_NAME) --data_dir $(HERE)/datasets

%.pth: kgat_pytorch/datasets/pretrain/$(DATA_NAME)/mf.npz
	cd kgat_pytorch && $(py) $(ALGO_PYTHON_SCRIPT_PYT) --use_pretrain 1 --evaluate_every 10 --Ks '[$(Ks)]' --data_name $(DATA_NAME) --data_dir $(HERE)/datasets

$(TRAINED_CLUSTER_OUTPUT) $(TRAINED_MODEL_OUTPUT) &: $(LATEST_PTH)
	$(MAKE) -C proc_clustering training CLUSTER_OUTPUT_DIR="$(CLUSTER_OUTPUT_DIR)" DATA_DIR="$(HERE)/datasets" DATA_NAME="$(DATA_NAME)" K="$(Ks)" LATEST_PTH="$(shell find $(ALGO_PTH_DIR) -newer kgat_pytorch -name '*.pth' -exec stat -c '%Y %n' {} \; | sort -nr | head -n 1 | cut -f2 -d' ')"

ifdef INIT
.PHONY: $(USERS_FILE)
$(USERS_FILE):
	mkdir -p $(USER_DATA_DIR) && $(shell echo "wisski_id\tfirst_seen" > $@)

.PHONY: $(INTERACTIONS_FILE)
$(INTERACTIONS_FILE):
	mkdir -p $(USER_DATA_DIR) && $(shell echo "wisski_user\twisski_item\tat" > $@)
else
$(USERS_FILE): 
	mkdir -p $(USER_DATA_DIR) && curl -X 'POST' --user $(PUB_ENDPOINT_USER):$(PUB_ENDPOINT_PASSWD) $(PUB_HOST)/maintenance/v1/db/export_users -H 'accept: text/tsv' -o $@

$(INTERACTIONS_FILE):
	mkdir -p $(USER_DATA_DIR) && curl -X 'POST' --user $(PUB_ENDPOINT_USER):$(PUB_ENDPOINT_PASSWD) $(PUB_HOST)/maintenance/v1/db/export_interactions -H 'accept: text/tsv' -o $@
endif

$(FINAL_MODEL_OUTPUT): $(USERS_FILE) $(TRAINED_MODEL_OUTPUT)
	mkdir -p $(FINAL_OUTPUT_DIR) && $(shell awk -v OFS=' ' -f $(HERE)/datasets/$(DATA_NAME)/res/convert_ids_to_wisski_model.awk $(ITEMS_FILE) $(USERS_FILE) $(TRAINED_MODEL_OUTPUT) > $@ ) 

$(FINAL_CLUSTER_OUTPUT): $(TRAINED_CLUSTER_OUTPUT)
	mkdir -p $(FINAL_OUTPUT_DIR) && $(shell awk -v OFS=' ' -f $(HERE)/datasets/$(DATA_NAME)/res/convert_ids_to_wisski_cluster.awk $(ITEMS_FILE) $(TRAINED_CLUSTER_OUTPUT) > $@ ) 

endif
