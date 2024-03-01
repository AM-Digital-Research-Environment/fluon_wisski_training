# fo_training

## Getting started

* Install prerequisits
* make sure to have a running instance of [dmkg/fluon-refsrv](https://gitlab.uni-bayreuth.de:dmkg/fluon-refsrv) running
* configure URL of instance in Makefile and adjust credentials of user in `Makefile.local`:
  ```
  PUB_DEST:=/some/personal/copy/of/the/folder
  PUB_ENDPOINT_PASSWD:=fluon-account-password-goes-here
  ```

* ```make publish```
* fix bugs :)

## Next Steps

right now, it is just the bare pipeline that works

### Inspect Knowledge Graph

is the KG really making sense right now? can it be filtered in terms of some network metrics? is it even a network or a tree atm? do we need all the entities?

### Sampling of training profiles

in [datasets/fill_interactions.py](datasets/fill_interactions.py) user interactions are sampled for training purposes. right now, this is done purely random. adjust this to some clever way. maybe some KG-informed walks that make up profiles? maybe create personas of how they traverse the KG and then sample from different personas.

### Modeling and Clustering

this needs some paramter tuning. right now, it is optimised to finish as quickly as possible and show that the pipeline works.

also, for new users, we just obtain the average of clustered items and rank them based on distance from the centroid. what kind of recommendation does this produce? can this be done better/different?

### Preparing Recommendations

Right now, it is a clustering of embeddings of entities (not just items, which is something different in the language of related works [kgat](kgat) and [kgat_pytorch](kgat_pytorch)) in [recommendations/train_cluster.py](recommendations/train_cluster.py). maybe this can be improved as well.

### Use and Filter Existing Interactions

Right now, the modeling is based on logged interactions from the database. they are downloaded and used for embedding. maybe this can be filtered to only use a user's last X interactions...
