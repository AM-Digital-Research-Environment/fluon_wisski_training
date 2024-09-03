#!/usr/bin/env python3

import torch
import numpy as np
import os
import logging
from joblib import dump, load

from tqdm import tqdm

from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MaxAbsScaler
# ~ from cuml.cluster import DBSCAN
from sklearn.cluster import OPTICS, cluster_optics_dbscan
from sklearn.model_selection import train_test_split
from sklearn import metrics
# ~ from cuml.metrics.pairwise_distances import pairwise_distances
from sklearn.metrics import pairwise_distances, silhouette_score
# ~ import cupy

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

import sys
sys.path.insert(0,'../../kgat_pytorch')
from model.KGAT import KGAT
from parser.parser_kgat import *
from data_loader.loader_kgat import DataLoaderKGAT
from utils.log_helper import *
from utils.metrics import *
from utils.model_helper import *

def train_cluster(model, data, outfile_clust, outfile_X):
  model.eval()

  item_ids = torch.arange(data.n_items, dtype=torch.long).cpu()
  emb = model.entity_user_embed.cpu()
  embeddings = emb(item_ids).detach().numpy()
  
  clust = OPTICS(metric = 'cosine')
  clust.fit(embeddings)
  
  dump(clust, outfile_clust)
  np.save(outfile_X, embeddings)
  

if __name__ == '__main__':
  args = parse_kgat_args()
  args.use_pretrain = 2
  
  # outdir = os.path.dirname(os.path.dirname(args.save_dir))
  outdir = os.getenv("CLUSTERING_OUT_DIR", None)
  if outdir is None:
    raise ValueError("Envvar CLUSTERING_OUT_DIR not specified, aborting")

  res_file_clust = os.path.join(outdir,'clustering.joblib')
  res_file_X     = os.path.join(outdir,'clustering_data.npy')
  torch.manual_seed(args.seed)

  # GPU / CPU
  # ~ device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  # load data
  data = DataLoaderKGAT(args, logging)

  # load model
  model = KGAT(args, data.n_users, data.n_entities, data.n_relations)
  model = load_model(model, args.pretrain_model_path)
  # ~ model.to(device)
  train_cluster(model, data, res_file_clust, res_file_X)
  # ~ evaluate(model, data.n_items, data.test_batch_size, data.test_user_dict, device)
