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

In [profile_sampler/profile_sampler.py](profile_sampler/profile_sampler.py), profiles are sampled according to three different personas. The number of sampled profiles depends on the number of real interactions logged in the [dmkg/fluon-refsrv](https://gitlab.uni-bayreuth.de:dmkg/fluon-refsrv) and the configuration of total number of required user profiles.

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

Profile sampling is configurable in the main [Makefile](Makefile). 

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

Right now, it is a clustering of embeddings of entities (not just items, which is something different in the language of related works [kgat](kgat) and [kgat_pytorch](kgat_pytorch)) in [recommendations/train_cluster.py](recommendations/train_cluster.py). maybe this can be improved as well.

### Use and Filter Existing Interactions

Right now, the modeling is based on logged interactions from the database. they are downloaded and used for embedding. maybe this can be filtered to only use a user's last X interactions...
