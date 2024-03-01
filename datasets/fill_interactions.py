#!/usr/bin/env python3

import random
from pathlib import Path

def main(kg_items_file, user_file, interactions_file, n_user,n_interact_min,n_interact_max,n_interact_test_max,outdir):
  n_user = int(n_user)
  n_interact_min = int(n_interact_min)
  n_interact_max = int(n_interact_max)
  n_interact_test_max = int(n_interact_test_max)
  assert n_interact_test_max < n_interact_max
  
  u_ids = {}
  if user_file is not None:
    with open(user_file) as _uf:
      _uf.readline()
      for i,line in enumerate(_uf):
        fields = line.strip().split('\t')
        u_ids[ int(fields[0]) ] =  i
  n_known_users = len(u_ids.keys())
  
  i_ids = {}
  with open(kg_items_file) as _i:
    _i.readline()
    for line in _i:
      fields = line.strip().split(' ')
      _id = int(fields[2])
      i_ids[_id] = int(fields[0])
  n_known_items = len(i_ids.keys())
  assert n_interact_max <= n_known_items
  
  interactions = {}
  if interactions_file is not None:
    with open(interactions_file) as _i:
      _i.readline()
      u_interactions = []
      last_u = None
      for line in _i:
        fields = line.strip().split('\t')
        user = int(fields[0])
        item = int(fields[1])
        if last_u is None:
          last_u = user
        if last_u != user:
          interactions[ u_ids[last_u] ] = u_interactions
          u_interactions = []
          last_u = user
        u_interactions.append( i_ids[item] )
      interactions[ u_ids[user] ] = u_interactions
  
  
  with open(Path(outdir,"train.txt").resolve(), 'w') as train_out, open(Path(outdir,"test.txt").resolve(), 'w') as test_out:
    for u in range(n_user):
      if u in interactions: # keep known users
        n = random.choice(range(1,min(n_interact_test_max+1,  len(interactions[u])-1))) # user interactions might be fewer. but we need data for testing nevertheless
        test = random.choices(interactions[u], k=n)
        train = list(set(interactions[u]) - set(test))
        print(u,' '.join(str(i) for i in test), file=test_out)
        print(u,' '.join(str(i) for i in train), file=train_out)
      else: # generate more if necessary
        n = random.choice(range(n_interact_min,n_interact_max+1))
        interactions = random.sample(range(0,n_known_items), k=n)
        n = random.choice(range(1,n_interact_test_max+1))
        test = random.choices(interactions, k=n)
        train = list(set(interactions) - set(test))
        print(u,' '.join(str(i) for i in test), file=test_out)
        print(u,' '.join(str(i) for i in train), file=train_out)


if __name__=='__main__':
  import plac
  plac.call(main)
