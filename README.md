# fo_training

## Getting started

* Install prerequisits
* make sure to have a running instance of [dmkg/fluon-refsrv](https://gitlab.uni-bayreuth.de:dmkg/fluon-refsrv) running
* configure URL of instance in Makefile and adjust credentials of user in `Makefile.local`:
  ```
  PUB_DEST:=/some/personal/copy/of/the/folder
  PUB_ENDPOINT_PASSWD:=fluon-account-password-goes-here
  ```

* ```INIT=1 make init && make publish```
* fix bugs :)

## Next Steps

Right now, the training-side of fluid ontologies works:

* Loading the entire knowledge graph from wisski
* Gathering user profiles from fluon-server
* Sampling knowledge graph informed profiles if there aren't enough existing user profiles
* Obtaining a ranking of items for existing users
* Clustering embedding vectors of items to obtain groups of items
* Rank items based on distance of cluster centroids
* Derive recommendations for new users based on cluster centroids

One characteristic of fluid ontologies is backpropagating frequent user interactions as possible updates of the ontology. This part is untackled, yet. One could inspect frequent user paths, however, and combine that with closeness derived from item embedding to identify items in the knowledge graph that share a similarity that hasn't been uncovered by ontological connections yet. 

### Inspect Knowledge Graph

is the KG really making sense right now? can it be filtered in terms of some network metrics? is it even a network or a tree atm? do we need all the entities?

Right now, the KG is obtained by downloading all statements from wisski. Then, some filtering is applied to the entities and to the relations by using blacklists for [entities](datasets/wisski/res/filter_predicates) and [relations](datasets/wisski/res/filter_relations). Also, the toolchain allows to filter out leaf-nodes in the knowledge graph which can be configured in the [dataset-related Makefile](datasets/wisski/Makefile) via

* `MIN_DEGREE_IN` (standard: 2) entities in the knowledge graph should have *at least* this many *incoming* connections
* `MIN_DEGREE_OUT` (standard: 2) entities in the knowledge graph should have *at least* this many *outgoing* connections

For subsequent modeling, clustering, and recommendation, it is necessary to distinguish between metadata *entities* of the KG and *items*, i.e. those entities that represent actual datasets suitable for recommendation. These items are fetched through [a SPARQL query](datasets/wisski/res/fetch_items.sparql) first and they are listed on top of the entities list in [entities_id.txt](datasets/wisski/entities_id.txt). The corresponding [items_id.txt](datasets/wisski/items_id.txt) is an overview over just the items (which is also required at other points like profile sampling).

Compilation of all the datafiles happens via `awk` and the recipe given in [datasets/wisski/res/nt_to_knowledge_graph.awk](datasets/wisski/res/nt_to_knowledge_graph.awk).

### Sampling of training profiles

In [proc_fluidontologies/sample_profiles.py](proc_fluidontologies/sample_profiles.py), profiles are sampled according to three different personas. The number of sampled profiles depends on the number of real interactions logged in the [dmkg/fluon-refsrv](https://gitlab.uni-bayreuth.de:dmkg/fluon-refsrv) and the configuration of total number of required user profiles.

#### KG-informed topic focus

This persona interacts with items that are closely related to an item of interest.

For profile sampling, the item of interest `i` is sampled randomly. Then, the knowledge graph is consulted to identify the `k`-hop neighborhood of `i`. The final profile consists of item `i` and `n` other sampled items out of the `k`-hop induced subgraph around `i`. 

The number of hops `k` is obtained from the distance matrix of the knowledge graph. It first creates a histogram of available distances in the graph and checks for which distance enough items are in reach. How many items are required is given through configuration: `N_USERS * PERC_WITHIN_RANGE / 100.0`.

#### KG-informed walks

This persona is modeled as someone who browses the database on the look for inspiration.

For profile sampling, a starting item `i` is sampled randomly. Then, another item `i2` is sampled that has a large distance to `i`. The knowledge graph is then queried to yield shortest paths between `i` and `i2` and all items along that path are added to the profile. This process continues with `i2` as the new starting point for path sampling until enough interactions are sampled.

#### Random interactions

This persona just clicks around randomly. The profile is simply sampled randomly.

#### Configuration

Profile sampling is configurable in the [proc_fluidontologies/Makefile](proc_fluidontologies/Makefile). 

* `N_USERS`: The total number of user profiles that is required for training. If the [dmkg/fluon-refsrv](https://gitlab.uni-bayreuth.de:dmkg/fluon-refsrv) already contains `N_AVAILABLE` real interactions, these are given priority. The number of required sampled profiles is obtained as the difference between `N_REQUIRED = N_USERS - N_AVAILABLE`.
* `PERC_WITHIN_RANGE`: percentage of profiles that are sampled according to the [focused persona](#kg-informed-topic-focus). The number of profiles is obtained as `N_REQUIRED * PERC_WITHN_RANGE / 100`
* `PERC_ALONG_PATHS`: percentage of profiles that are sampled according to the [browsing persona](#kg-informed-walks). The number of profiles is obtained as `N_REQUIRED * PERC_ALONG_PATHS / 100`
* `N_INTERACT_MAX`: the maximum number of interactions (i.e. items) the profiles should have 
* `N_INTERACT_MIN`: the minimum number of interactions (i.e. items) the profiles should have 
* `N_INTERACT_MAX_TEST`: the number of interactions that are randomly taken out of the profile to the test data.

### Modeling and Clustering

this needs some paramter tuning. right now, it is optimised to finish as quickly as possible and show that the pipeline works.

also, for new users, we just obtain the average of clustered items and rank them based on distance from the centroid. what kind of recommendation does this produce? can this be done better/different?

### Preparing Recommendations

Right now, it is a clustering of embeddings of entities (not just items, which is something different in the language of related works [kgat](kgat) and [kgat_pytorch](kgat_pytorch)) in [proc_clustering/cluster_training.py](proc_clustering/cluster_training.py). maybe this can be improved as well.

### Use and Filter Existing Interactions

Right now, the modeling is based on logged interactions from the database. they are downloaded and used for embedding. maybe this can be filtered to only use a user's last X interactions...
