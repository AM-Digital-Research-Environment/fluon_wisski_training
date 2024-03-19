from collections import defaultdict
import nctx.undirected as nctx
import numpy as np
import random
from pathlib import Path
import logging 

class KnowledgeGraph():
  
  def __init__(self, args):
    self.g = nctx.Graph()
    self.ids = set()
    self.items = set()
    self.n_items = 0
    self.n_entities = 0
    
    kg_dir = Path(args.knowledge_graph_file).parent
    self.dist_p = Path(kg_dir, 'distance_map.npy')
  
  def get_distance_map_path(self):
    return self.dist_p
  
  def load(self, args):
    vertices = defaultdict(lambda: self.g.add_vertex())
    with open(args.items_file, 'r') as _items:
      _items.readline()
      for line in _items:
        self.items.add(
          int(line.strip().split(' ')[0])
        )
    for i in self.items:
      vertices[i]
    self.n_items = len(self.items)
    
    with open(args.entities_file, 'r') as _entities:
      _entities.readline()
      for line in _entities:
        self.ids.add(
          int(line.strip().split(' ')[0])
        )
    for i in self.ids:
      vertices[i]
    self.n_entities = len(self.ids)
     
    with open(args.knowledge_graph_file, 'r') as _kg:
      for i,line in enumerate(_kg):
        line = line.strip().split(' ')
        u = int(line[0])
        v = int(line[2])
        assert(u in self.ids)
        assert(v in self.ids)
        
        if v not in self.g.children(u):
          self.g.add_edge(u,v)
          
  def get_distance_map(self):
    def decision(start, l, r):
      return True
    logger.debug("obtaining distance map now")
    self.distance_map = np.full((self.n_items, self.n_items), -1)
    for u in range(self.n_items):
      sp_ctx = np.asarray(nctx.AlgPaths.dijkstra_ctx(self.g, u, decision))
      sp_ctx[np.where(sp_ctx < 0)] = -1
      self.distance_map[u,:] = sp_ctx[0:self.n_items]
    logger.debug("obtaining distance map done")
  
  def get_graph(self):
    return self.g
  
  def get_path_between_items(self, start, target):
    sp = nctx.AlgPaths.find_path(self.g, int(start), int(target))
    items = self.filter_items(sp)
    return items
  
  def get_items_in_range(self, u, nw_range_max, nw_range_min=0):
    nonz = ((self.distance_map[u,:] >= nw_range_min) & (self.distance_map[u,:] <= nw_range_max)).nonzero()[0]
    return nonz
  
  def sample_n_items(self, n):
    # ~ logger.debug("sampling random items")
    return random.choices(range(self.n_items), k=n)
  
  def filter_items(self, arr):
    if not isinstance(arr, np.ndarray):
      arr = np.asarray(arr)
    return arr[np.where((arr >= 0) & (arr <= self.n_items))]

  def dist_hist(self):
    lower = np.tril(self.distance_map, k=0)
    lower = np.reshape(lower, lower.size)
    lower = lower[np.where(lower>0)]
    hist = np.bincount(lower)
    cs = (np.cumsum(hist)>0).nonzero()[0]
    return hist, np.min(cs), np.max(cs)
  
  def get_min_plausible_dist(self, n_wanted):
    hist, _, _ = self.dist_hist()
    cs = np.cumsum(hist) >= n_wanted
    if np.any(cs):
      # in this case, we found a position that satisfies condition >= n_wanted
      i = np.argmax(cs)
      return i
    else:
      # in this case, the cumulative sum of hist doesn't contain a value >= n_wanted
      return -1
  
  def __str__(self):
    return f"KnowledgeGraph contains {self.n_entities} entities in total of which {self.n_items} are items. KG has now {self.g.numVertices()} vertices and {self.g.numEdges()} edges"
    
  def save(self, p):
    np.save(p, self.distance_map)
    
  def load_map_and_check(self, p):
    self.distance_map = np.load(p)
    shp = self.distance_map.shape
    assert(shp[0]==shp[1])
    assert(shp[0]==self.n_items)
    assert(shp[0]>=len(self.items))
