#!/usr/bin/env python3

import logging
from pathlib import Path

BASE = Path(__file__).stem
logger = logging.getLogger(BASE)

import os

from joblib import dump, load

import numpy as np
from sklearn.cluster import OPTICS, cluster_optics_dbscan
from sklearn import metrics
from sklearn.metrics import silhouette_score

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

def evaluate_cluster(args):
  clust = load(args.cluster)
  X = np.load(args.data)
  
  # obtain different cluster configurations via DBscan and obtain silhouette coefficient
  sil = []
  ran = np.linspace(0.01, 1.0, num=20, endpoint=True)
  for e in ran:
      labels = cluster_optics_dbscan(
        reachability=clust.reachability_,
        core_distances=clust.core_distances_,
        ordering=clust.ordering_,
        eps=e,
      )
      if len(np.unique(labels)) > 1:
          sil.append(silhouette_score(X, labels))
      else:
          sil.append(0)
  
  # extract optimal configuration according to silhouette coefficient
  # ~ eps = ran[np.argmax(sil)]
  # but use highest configuration of silhouette coefficient possible. therefore,
  # create a reversed view of both ran and sil to get the highest value of silhouette
  # coefficient possible
  eps = ran[::-1][np.argmax(sil[::-1])]
  labels = cluster_optics_dbscan(
    reachability=clust.reachability_,
    core_distances=clust.core_distances_,
    ordering=clust.ordering_,
    eps=eps,
  )

  # gather cluster assignments and ranks inside clusters for items
  # start with outliers that have cluster assignment -1
  outliers = (labels==-1).nonzero()[0]
  # index, cluster, rank
  out = np.array((outliers,
                  np.full(len(outliers),-1),
                  np.full(len(outliers),-1)))
  k = len(np.unique(labels[labels>-1]))
  for i in range(k):
      l = (labels==i).nonzero()[0]
      if len(l) > 1:
          # we have more than one item in the cluster
          # obtain centroid
          centroid = np.mean(X[l], axis=0)
          # measure distance to centroid
          d = X[l] - centroid
          # sum squared errors
          d = np.sum(np.power(d, 2), axis=1)
          # use that sum to sort indices of cluster items
          d = d.argsort()
          ranks = np.empty_like(d)
          ranks[d] = np.arange(len(d))
          out = np.append(out, np.array((l,                       # index
                                         np.full(len(l),i),       # cluster
                                         ranks)), axis=1)         # rank
      else:
          out = np.append(out, np.array((l,                       # index
                                         np.full(1,i),            # cluster
                                         np.full(1,0))), axis=1)  # rank
  out = out.T
  out.sort(axis=0)
  
  p = os.path.join(
        os.path.dirname(args.outfile),
        os.path.splitext(os.path.basename(args.outfile))[0]+'.npy'
      )
  
  np.save(p,
          out.astype(int))
  np.savetxt(args.outfile,
             out.astype(int),
             delimiter=' ',
             fmt='%i',
             header='item cluster rank')

def get_log_filename(out_dir, base=BASE, ext='.log'):
  def get_basename(log_id, base=BASE, ext='.log'):
    return '{}_{:d}{}'.format(base,log_id,ext)
  
  log_count = 0
  f = Path(out_dir, get_basename(log_count))
  while f.exists():
    log_count += 1
    f = Path(out_dir, get_basename(log_count))
  return f.resolve()

def configure_logging(args):
  if args.log_to_file:
    p = Path(args.log_dir)
    p.mkdir(parents=True, exist_ok=True)
  for handler in logging.root.handlers:
    logging.root.removeHandler(handler)
  logging.root.handlers = []
  logging.root.setLevel(args.log_level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  
  if args.log_to_file:
    logfile = logging.FileHandler(get_log_filename(args.log_dir))
    logfile.setFormatter(formatter)
    logging.root.addHandler(logfile)

  if not args.log_to_console_off:
    logconsole = logging.StreamHandler()
    logconsole.setFormatter(formatter)
    logging.root.addHandler(logconsole)

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description="Run this thing.")

  parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="log_level", const=logging.DEBUG,
    default=logging.WARNING)
  
  parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const", dest="log_level", const=logging.INFO)
                      
  parser.add_argument(
    '--log_to_file', 
    action='store_true',
    help='Redirect log to file')
                      
  parser.add_argument(
    '--log_to_console_off', 
    action='store_true',
    help='Turn off console output')
                      
  parser.add_argument(
    '--log_dir', 
    nargs='?', 
    default='logs',
    help='choose logging directory')
                      
  parser.add_argument(
    '--cluster', 
    help='clusterfile', 
    required = True)
                      
  parser.add_argument(
    '--data', 
    help='datafile', 
    required = True)
                      
  parser.add_argument(
    '--outfile', 
    nargs='?', 
    default='cluster.csv',
    help='file containing cluster assignments of items')
                    
  args = parser.parse_args()
  configure_logging(args)
  
  evaluate_cluster(args)

