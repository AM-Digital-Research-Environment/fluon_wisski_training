# dataset to be used. must have a folder in datasets/
DATA_NAME:=wisski
#FORCE:=force
# set to 'force' to force rebuild by fetching user and interaction data
FORCE:='no'
# can be adjusted to KGAT or CKE
ALGO:=KGAT

# how many user profiles should we have for training? required profiles will be sampled
N_USERS:=300
# percentage of profiles that are modeled browsing around the KG neighborhood of random items
PERC_WITHIN_RANGE:=50
# percentage of profiles that are modeled browsing along paths in KG
PERC_ALONG_PATHS:=50
# number of interactions the profiles should have at max
N_INTERACT_MAX:=200
# and at min
N_INTERACT_MIN:=30
# and out of the max number, this many will be put into the test set
N_INTERACT_MAX_TEST:=10

# config paths
HERE:=${CURDIR}
REMOTE_BASE_DIR:=$(HERE)
SAVE_DIR:=trained_model/$(ALGO)/$(DATA_NAME)
PUB_DEST:=/path/to/destination/
PUB_HOST:=http://127.0.0.1:5000
PUB_ENDPOINT_USER:=dmkg
#NOSYNC:=$(HERE)/403.23.99__tmp
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
RSYNC_SETTINGS:=-av --delete --exclude $(shell basename $(NOSYNC)) --exclude *docker-compose.yml
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

LATEST_PTH:=$(shell find $(ALGO_PTH_DIR) -newer kgat_pytorch -name '*.pth' -exec stat -c '%Y %n' {} \; | sort -nr | head -n 1 | cut -f2 -d' ')
TRAINED_CLUSTER:=$(HERE)/recommendations/trained_model/$(ALGO)/$(DATA_NAME)/clustering.joblib
TRAINED_CLUSTER_DATA:=$(HERE)/recommendations/trained_model/$(ALGO)/$(DATA_NAME)/clustering_data.npy
TRAINED_CLUSTER_OUTPUT:=$(HERE)/recommendations/trained_model/$(ALGO)/$(DATA_NAME)/cluster.csv
TRAINED_MODEL_OUTPUT:=$(HERE)/recommendations/trained_model/$(ALGO)/$(DATA_NAME)/recommendations.csv
CLUSTER_OUTPUT_DIR:=$(HERE)/recommendations/trained_model/$(ALGO)/$(DATA_NAME)/
FINAL_OUTPUT_DIR:=$(HERE)/pub/$(DATA_NAME)/
FINAL_MODEL_OUTPUT:=$(FINAL_OUTPUT_DIR)/recommendations.csv
FINAL_CLUSTER_OUTPUT:=$(FINAL_OUTPUT_DIR)/cluster.csv
USER_DATA_DIR:=$(HERE)/datasets/fluon_refsrv
USERS_FILE=$(USER_DATA_DIR)/user_ids.tsv
INTERACTIONS_FILE=$(USER_DATA_DIR)/user_interactions.tsv

ifeq ($(DATA_NAME),wisski)
Ks:=20, 40, 60, 80, 100
KG_ITEMS_FILE:=items_id.txt
else
$(error DATA_NAME must be 'wisski')
endif
KG_ITEMS_N:=$(shell cut -f2 $(HERE)/datasets/$(DATA_NAME)/$(KG_ITEMS_FILE) | sort -nrk1,1 | head -1 | awk '{print $$1 + 1}') # increment result by one as numbering starts at 0

#~ .INTERMEDIATE: $(DIRNE)/config.py

all:
	$(info nothing to be done here...)

ifdef REMOTE
.PHONY: clean output sync_here sync_to_remote test
output: sync_to_remote
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
init: $(USERS_FILE) $(INTERACTIONS_FILE) datasets/wisski/kg_final.txt datasets/wisski/train.txt
	rm -f $(FINAL_CLUSTER_OUTPUT) $(FINAL_MODEL_OUTPUT)
	rm -f -r recommendations/trained_model/$(ALGO)/$(DATA_NAME)
	rm -f -r kgat/Model/pretrain/$(DATA_NAME)
	rm -f -r kgat/Model/weights/$(DATA_NAME)
	rm -f -r kgat_pytorch/datasets/pretrain/$(DATA_NAME)
	rm -f -r kgat_pytorch/trained_model/$(ALGO)/$(DATA_NAME)
	$(info initialized. sure you ran everything with INIT=1 as environment variable?)

.PHONY: find_ref
find_ref:
	rm -f find_ref && touch find_ref

changelist:
	$(shell find . ! -path . -newermm find_ref -print > changelist && rm -f find_ref)

output: find_ref $(FINAL_CLUSTER_OUTPUT) $(FINAL_MODEL_OUTPUT) changelist
	$(info done)

.PHONY: publish
publish: $(FINAL_CLUSTER_OUTPUT) $(FINAL_MODEL_OUTPUT)
	$(PUB_COMMAND) $(HERE)/datasets/$(DATA_NAME)/items_id.txt $(PUB_DEST)/items_id.txt && \
	$(PUB_COMMAND) $^ $(PUB_DEST) && \
	curl -X POST -H 'accept: application/json' --user $(PUB_ENDPOINT_USER):$(PUB_ENDPOINT_PASSWD) $(PUB_HOST)$(PUB_ENDPOINT_TRIGGER_UPDATE) | grep -v true  && echo "success" || echo "failure in update"

clean:
	rm -f recommendations/clustering.joblib recommendations/clustering_data.npy

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

datasets/wisski/train.txt: $(USERS_FILE) $(INTERACTIONS_FILE)
	cd profile_sampler && python3 profile_sampler.py -d --n_interact_min $(N_INTERACT_MIN) --n_interact_max $(N_INTERACT_MAX) --n_interact_test_max $(N_INTERACT_MAX_TEST) --n_profiles $(N_USERS) --perc_within_range $(PERC_WITHIN_RANGE) --perc_along_path $(PERC_ALONG_PATHS) --items_file $(HERE)/datasets/$(DATA_NAME)/items_id.txt --knowledge_graph_file $(HERE)/datasets/$(DATA_NAME)/kg_final.txt --entities_file $(HERE)/datasets/$(DATA_NAME)/entities_id.txt --user_file $(USERS_FILE) --interactions_file $(INTERACTIONS_FILE) --save_dir $(HERE)/datasets/$(DATA_NAME)

datasets/wisski/kg_final.txt:
	cd datasets/wisski && make kg

kgat/Model/pretrain/$(DATA_NAME)/mf.npz: kgat datasets/$(DATA_NAME)/kg_final.txt datasets/$(DATA_NAME)/train.txt
	cd kgat && ( [ -d Data/$(DATA_NAME) ] || ln -s $(HERE)/datasets/$(DATA_NAME) Data/$(DATA_NAME) ) && cd Model && \
	python3 Main.py $(ALGO_PARAMS) --model_type bprmf --save_flag 1 --pretrain -1 --report 0 && python3 Main.py $(ALGO_PARAMS) --model_type bprmf --save_flag -1 --pretrain 1 --report 0

kgat_pytorch/datasets/pretrain/$(DATA_NAME)/mf.npz: kgat_pytorch kgat/Model/pretrain/$(DATA_NAME)/mf.npz
	[ -f $@ ] || ( mkdir -p kgat_pytorch/datasets/pretrain/$(DATA_NAME) && ln -s $(HERE)/kgat/Model/pretrain/$(DATA_NAME)/mf.npz $@ )

.PHONY: train_kgat
train_kgat: kgat/Model/pretrain/$(DATA_NAME)/mf.npz
	cd kgat/Model && python3 Main.py $(ALGO_PARAMS) --model_type $(ALGO_PYTHON_PARAM_MODELTYPE) --pretrain -1 --save_flag 1 --report 0

.PHONY: train_kgat_pytorch
train_kgat_pytorch: kgat_pytorch/datasets/pretrain/$(DATA_NAME)/mf.npz
	cd kgat_pytorch && python3 $(ALGO_PYTHON_SCRIPT_PYT) --use_pretrain 1 --evaluate_every 10 --Ks '[$(Ks)]' --data_name $(DATA_NAME) --data_dir $(HERE)/datasets

%.pth: kgat_pytorch/datasets/pretrain/$(DATA_NAME)/mf.npz
	cd kgat_pytorch && python3 $(ALGO_PYTHON_SCRIPT_PYT) --use_pretrain 1 --evaluate_every 10 --Ks '[$(Ks)]' --data_name $(DATA_NAME) --data_dir $(HERE)/datasets

$(TRAINED_CLUSTER): $(LATEST_PTH) $(CLUSTER_OUTPUT_DIR) 
	cd recommendations && python3 train_cluster.py --data_name $(DATA_NAME) --data_dir $(HERE)/datasets --Ks '[$(Ks)]' --pretrain_model_path $(shell find $(ALGO_PTH_DIR) -newer kgat_pytorch -name '*.pth' -exec stat -c '%Y %n' {} \; | sort -nr | head -n 1 | cut -f2 -d' ')

$(TRAINED_CLUSTER_OUTPUT): $(TRAINED_CLUSTER)
	cd recommendations && python3 inspect_cluster.py --cluster $(TRAINED_CLUSTER) --data $(TRAINED_CLUSTER_DATA) --outfile $@

$(TRAINED_MODEL_OUTPUT): $(ALGO_PTH_DIR)/*.pth
	cd recommendations && python3 recommend.py --data_name $(DATA_NAME) --data_dir $(HERE)/datasets --Ks '[$(Ks)]' --pretrain_model_path $(shell find $(ALGO_PTH_DIR) -newer kgat_pytorch -name '*.pth' -exec stat -c '%Y %n' {} \; | sort -nr | head -n 1 | cut -f2 -d' ')

$(FINAL_OUTPUT_DIR):
	mkdir -p $@

$(CLUSTER_OUTPUT_DIR):
	mkdir -p $@

$(USER_DATA_DIR):
	mkdir -p $@

ifdef INIT
.PHONY: $(USERS_FILE)
$(USERS_FILE): $(USER_DATA_DIR)
	$(shell echo "wisski_id\tfirst_seen" > $@)

.PHONY: $(INTERACTIONS_FILE)
$(INTERACTIONS_FILE): $(USER_DATA_DIR)
	$(shell echo "wisski_user\twisski_item\tat" > $@)
else
$(USERS_FILE): $(USER_DATA_DIR)
	curl -X 'POST' --user $(PUB_ENDPOINT_USER):$(PUB_ENDPOINT_PASSWD) $(PUB_HOST)/maintenance/v1/db/export_users -H 'accept: text/tsv' -o $@

$(INTERACTIONS_FILE): $(USER_DATA_DIR)
	curl -X 'POST' --user $(PUB_ENDPOINT_USER):$(PUB_ENDPOINT_PASSWD) $(PUB_HOST)/maintenance/v1/db/export_interactions -H 'accept: text/tsv' -o $@
endif

$(FINAL_MODEL_OUTPUT): ITEMS_FILE=$(HERE)/datasets/$(DATA_NAME)/items_id.txt
$(FINAL_MODEL_OUTPUT): $(FINAL_OUTPUT_DIR) $(USERS_FILE) $(TRAINED_MODEL_OUTPUT)
	$(shell awk -v OFS=' ' -f $(HERE)/datasets/$(DATA_NAME)/res/convert_ids_to_wisski_model.awk $(ITEMS_FILE) $(USERS_FILE) $(TRAINED_MODEL_OUTPUT) > $@ ) 

$(FINAL_CLUSTER_OUTPUT): ITEMS_FILE=$(HERE)/datasets/$(DATA_NAME)/items_id.txt
$(FINAL_CLUSTER_OUTPUT): $(FINAL_OUTPUT_DIR) $(TRAINED_CLUSTER_OUTPUT)
	$(shell awk -v OFS=' ' -f $(HERE)/datasets/$(DATA_NAME)/res/convert_ids_to_wisski_cluster.awk $(ITEMS_FILE) $(TRAINED_CLUSTER_OUTPUT) > $@ ) 

endif
