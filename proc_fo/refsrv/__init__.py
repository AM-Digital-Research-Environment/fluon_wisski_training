#!/usr/bin/env python3

import random
from pathlib import Path

import logging 
BASE = Path(__file__).parent.stem
logger = logging.getLogger(BASE)

class RefSrvSampler():
  
  def __init__(self, args):
    self.args = args
    assert(self.args.interactions_file is not None)
    assert(self.args.user_file is not None)
    self.u_ids = None
    self.load_user_file()
  
  def load_user_file(self):
    self.u_ids = {}
    with open(self.args.user_file) as _uf:
      _uf.readline()
      for i,line in enumerate(_uf):
        fields = line.strip().split('\t')
        self.u_ids[ int(fields[0]) ] =  i
    self.n_known_users = len(self.u_ids.keys())
  
  def sample_interactions(self, outfile_train, outfile_test):
    assert(self.args.interactions_file is not None)
    assert(self.args.user_file is not None)
    
    i_ids = {}
    with open(self.args.items_file) as _i:
      _i.readline()
      for line in _i:
        fields = line.strip().split(' ')
        _id = int(fields[2])
        i_ids[_id] = int(fields[0])
    n_known_items = len(i_ids.keys())
    assert self.args.n_interact_max <= n_known_items
    
    interactions = {}
    with open(self.args.interactions_file) as _i:
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
          interactions[ self.u_ids[last_u] ] = u_interactions
          u_interactions = []
          last_u = user
        u_interactions.append( i_ids[item] )
      interactions[ self.u_ids[user] ] = u_interactions
  
    n_sampled = 0
    for u in range(self.n_known_users):
      if u in interactions:
        n = random.choice(range(1,min(self.args.n_interact_test_max+1,  len(interactions[u])-1))) # user interactions might be fewer. but we need data for testing nevertheless
        test = random.choices(interactions[u], k=n)
        train = list(set(interactions[u]) - set(test))
        print(u,' '.join(str(i) for i in test), file=outfile_test)
        print(u,' '.join(str(i) for i in train), file=outfile_train)
        n_sampled+=1
    return n_sampled

