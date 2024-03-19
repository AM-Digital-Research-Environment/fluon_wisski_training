#!/usr/bin/env python3

import logging
import random
from pathlib import Path

BASE = Path(__file__).stem
logger = logging.getLogger(BASE)

from graph.GraphSampler import GraphSampler
from refsrv import RefSrvSampler
from procutils import *


def prepare_and_sample_from_kg(args, n_already_sampled, outfile_train, outfile_test):
  p = Path(args.save_dir)
  p.mkdir(parents=True, exist_ok=True)
  
  kg = GraphSampler(args)
  kg.load(args)
  logger.debug(kg)
  
  p = kg.get_distance_map_path()
  
  if p.exists():
    kg.load_map_and_check(p.resolve())
  else:
    kg.get_distance_map()
    kg.save(p.resolve())
  
  hist,min_dist_nonzero, max_dist_nonzero = kg.dist_hist()
  
  logger.info("  sampling ego-network based profiles")
  # sample items from item ego-networks
  # modeling people who are rather focused on a particular topic
  min_plausible_dist = kg.get_min_plausible_dist(args.n_interact_max)
  if min_plausible_dist < 0:
    min_plausible_dist = max_dist_nonzero
  for i in range(args.n_within_range):
    only_zeros = True
    while only_zeros:
      # sample a random item
      items = kg.sample_n_items(args.n_within_range)
      for item in items:
        # look around the range-neighborhood of that random item. zero range doesn't make sense as there is a >= check inside
        ids = kg.get_items_in_range(item,nw_range_min=1,nw_range_max=min_plausible_dist+1)
        if len(ids) > 0:
          logger.debug(f"    {i}th profile egn")
          # and distribute items from neighborhood to train and test lists
          train, test = sample_test_train(args, list(ids))
          if train is not False and test is not False:
            only_zeros = False
            print(f"{i} {' '.join([str(j) for j in train])}", file=outfile_train)
            print(f"{i} {' '.join([str(j) for j in test])}", file=outfile_test)
            n_already_sampled += 1
            break

  logger.info("  sampling path-based profiles")
  # sample items from item paths
  # modeling people who are rather focused on a particular topic
  for i in range(n_already_sampled, args.n_along_path+n_already_sampled):
    only_zeros = True
    while only_zeros:
      # sample random items
      items = kg.sample_n_items(args.n_along_path)
      for item in items:
        path = kg.sample_path_of_len(item,args.n_interact_max, min_dist_nonzero, max_dist_nonzero, unique_path=True)
        if len(path) >= args.n_interact_min:
          logger.debug(f"    {n_already_sampled}th profile pth")
          # and distribute items from neighborhood to train and test lists
          train, test = sample_test_train(args, list(path))
          if train is not False and test is not False:
            only_zeros = False
            print(f"{i} {' '.join([str(j) for j in train])}", file=outfile_train)
            print(f"{i} {' '.join([str(j) for j in test])}", file=outfile_test)
            n_already_sampled += 1
            break 
  
  logger.info("  sampling remaining random profiles")
  if args.n_rand > 0:
    # sample random items
    for i in range(n_already_sampled, args.n_rand+n_already_sampled):
      # sample random items
      items = kg.sample_n_items(args.n_interact_max)
      if len(items) > args.n_interact_min:
        train, test = sample_test_train(args, list(path))
        if train is not False and test is not False:
          print(f"{i} {' '.join([str(j) for j in train])}", file=outfile_train)
          print(f"{i} {' '.join([str(j) for j in test])}", file=outfile_test)
          n_already_sampled += 1
          break
  return n_already_sampled

def main(args):
  sample_real_profiles = args.user_file is not None
  rp_sampler = None
  rp_n_known = -1
  if sample_real_profiles:
    rp_sampler = RefSrvSampler(args)
    rp_n_known = rp_sampler.n_known_users
  
  args = plausible_checks_for_args(args, sample_real_profiles, rp_n_known)
  logger.info(args)
  
  n_already_sampled = 0
  
  try:
    with open(Path(args.save_dir, 'train.txt'), 'w') as _train, open(Path(args.save_dir, 'test.txt'), 'w') as _test:
      if sample_real_profiles and rp_n_known > 0:
        logger.info("sampling real profiles now")
        n_already_sampled = rp_sampler.sample_interactions(_train, _test)
        logger.info("sampling real profiles done")
      
      if args.use_kg_sampling:
        logger.info("sampling KG-informed profiles now")
        n_already_sampled = prepare_and_sample_from_kg(args, n_already_sampled, _train, _test)
        logger.info("sampling KG-informed profiles done")
  except:
    Path(args.save_dir, 'train.txt').unlink(missing_ok=True)
    Path(args.save_dir, 'test.txt').unlink(missing_ok=True)
    logger.warning(f"an error occurred. removed train.txt and test.txt")
    return
  logger.info(f"done sampling {n_already_sampled} user profiles in total")
      
def parse_args():
  parser = get_preconfigured_parser()
  parser.add_argument('--n_profiles',            default=100, type=int, help='number of profiles to sample in total')
  parser.add_argument('--perc_within_range',     default= 50.0, type=float, help='percentage of profiles that will be sampled from network proximity of random items. if perc_within_range and perc_along_path do not add up to 100%, the rest will be sampled randomly')
  parser.add_argument('--perc_along_path',       default= 50.0, type=float, help='percentage of profiles that will be sampled from network paths of items. if perc_within_range and perc_along_path do not add up to 100%, the rest will be sampled randomly')

  parser.add_argument('--n_interact_max',        default=200, type=int, help='maximum number of interactions per sampled profile')
  parser.add_argument('--n_interact_min',        default= 30, type=int, help='minimal number of interactions per sampled profile')
  parser.add_argument('--n_interact_test_max',   default= 10, type=int, help='maximum number of interactions per sampled profile that go to the test set')
  
  return parser.parse_args()
                
  
if __name__ == '__main__':
  args = parse_args()
  
  configure_logging(args, BASE)
  
  main(args)

