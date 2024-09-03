#!/usr/bin/env python3

import torch
import numpy as np
import os
import logging

import sys
sys.path.insert(0,'../../../kgat_pytorch')
from model.KGAT import KGAT
from parser.parser_kgat import *
from data_loader.loader_kgat import DataLoaderKGAT
from utils.log_helper import *
from utils.metrics import *
from utils.model_helper import *

def evaluate(model, n_items, n_entities, test_batch_size, test_user_dict, device, outdir):
    model.eval()

    user_ids = list(test_user_dict.keys())
    user_ids_batches = [user_ids[i: i + test_batch_size] for i in range(0, len(user_ids), test_batch_size)]
    user_ids_batches = [torch.LongTensor(d) for d in user_ids_batches]

    item_ids = torch.arange(n_items, dtype=torch.long).to(device)
    
    out = None
    
    for batch_user_ids in user_ids_batches:
        batch_user_ids = batch_user_ids.to(device)
        
        
        with torch.no_grad():
            batch_scores = model(batch_user_ids, item_ids, mode='predict')       # (n_batch_users, n_items)

        batch_scores = batch_scores.cpu()
        
        try:
            _, rank_indices = torch.sort(batch_scores.cuda(), descending=True)    # try to speed up the sorting process
            rank_indices = rank_indices.cpu()
        except:
            _, rank_indices = torch.sort(batch_scores, descending=True)
        
        batch_user_ids = batch_user_ids.cpu()
        rank_indices = rank_indices.numpy()
        
        l = rank_indices.shape[1]
        ranks = np.arange(0,l)

        def collect_table(i,u):
            idx = rank_indices[i,:]
            items = item_ids[idx]
            items = items.cpu()
            return np.array((
                np.full(l,u-n_entities),  # repeat user id
                items.numpy(), # item ids are sorted at this point
                ranks          # save rank of item id
            )).T
        
        if out is None:
          out = np.concatenate([collect_table(i,u) for i,u in enumerate(batch_user_ids)])
        else:
          ranks = np.concatenate([collect_table(i,u) for i,u in enumerate(batch_user_ids)])
          out = np.concatenate([out,ranks])
        
        
    np.save(os.path.join(outdir,'recommendations.npy'), out)
    np.savetxt(os.path.join(outdir,'recommendations.csv'),
               out.astype(int),
               delimiter=',',
               fmt='%i',
               header='user item rank')          


if __name__ == '__main__':
  args = parse_kgat_args()
  args.use_pretrain = 2
  
  torch.manual_seed(args.seed)

  log_save_id = create_log_id(args.save_dir)
  logging_config(folder=args.save_dir, name='log{:d}'.format(log_save_id), no_console=False)
  logging.info(args)

  # GPU / CPU
  device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

  # load data
  data = DataLoaderKGAT(args, logging)

  # load model
  model = KGAT(args, data.n_users, data.n_entities, data.n_relations)
  model = load_model(model, args.pretrain_model_path)
  model.to(device)
  
  # outdir = os.path.dirname(os.path.dirname(args.save_dir))
  outdir = os.getenv("RECO_RAW_DIR", None)
  evaluate(model, data.n_items, data.n_entities, data.test_batch_size, data.test_user_dict, device, outdir)
