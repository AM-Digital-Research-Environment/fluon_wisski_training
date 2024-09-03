from . import KnowledgeGraph

from collections import defaultdict
import nctx.undirected as nctx
import numpy as np
import random
from pathlib import Path
import logging 

class GraphSampler(KnowledgeGraph):
  
  def __init__(self, args):
    super().__init__(args)
    self.g = super().get_graph()
  
  def sample_path_of_len(self, start, n, look_within_range_min, look_within_range_max, unique_path = True):
    path = []
    dead_ends = []
    while len(path) < n:
      # get all items as far away as possible
      targets = self.get_items_in_range(start,nw_range_min=look_within_range_min,nw_range_max=look_within_range_max)
      if len(targets) > 0:
        if len(path) == 0:
          # we can start a new path
          path.append(start)
          # sample a random target from reachable iitems
        target = np.random.choice(targets)
        if target in dead_ends or (unique_path and target in path):
          # update target if we visited that before and user wants a unique path or if we found that the target didn't lead us anywhere
          possible_targets = np.in1d(targets, path)
          if possible_targets.any():
            # we have at least one target that is not already in path
            i_target = np.random.choice(possible_targets.nonzero()[0])
            target = targets[i_target]
          else:
            # current start has been a dead end - we can't find a target worth investigating
            # so, last element of path is removed
            dead_ends.append( path.pop() )
            # and new start is going to be the previous to last target
            start = path[-1]
            continue
        # get a path between start and target
        new_segment = self.get_path_between_items(start, target)
        # first element of new_segment will be start. but that is already in path. keep rest
        path.extend(new_segment[1:])
        # update start to continue search from last target
        start = target
      else:
        break
    return path
    
  
