#!/usr/bin/env python3

import logging
import random
from pathlib import Path

from graph import KnowledgeGraph
from refsrv import RefSrvSampler

BASE = Path(__file__).stem
logger = logging.getLogger(BASE)

def plausible_checks_for_args(args, sample_real_profiles, n_real_profiles):
  N       = args.n_profiles
  N_LEFT  = args.n_profiles
  
  if sample_real_profiles:
    assert(n_real_profiles >= 0)
    assert(N > n_real_profiles)
    N_LEFT = N - n_real_profiles
    
  args.use_kg_sampling = N_LEFT > 0
  if args.use_kg_sampling:
    w_range = args.perc_within_range
    w_paths = args.perc_along_path
    
    assert(w_range <= 100)
    assert(w_paths <= 100)
    assert((w_paths+w_range) <= 100)
    
    n_range = int((w_range/100) * N_LEFT)
    n_paths = int((w_paths/100) * N_LEFT)
    
    p_rand = w_paths+w_range
    if (n_range + n_paths) < N_LEFT:
      p_rand += N_LEFT - (n_range + n_paths)
    if p_rand < 100:
      args.n_rand = int(N_LEFT * (100 - (p_rand))/100)
    else:
      args.n_rand = 0
    
    args.n_within_range = n_range
    args.n_along_path = n_paths
    if (args.n_rand + args.n_within_range + args.n_along_path) < N_LEFT:
      args.n_rand += N_LEFT - (args.n_rand + args.n_within_range + args.n_along_path)
  return args

def sample_test_train(args, a_list):
  real_max = args.n_interact_max+1
  real_max = min(real_max, len(a_list))
  real_min = args.n_interact_min
  
  if real_min > real_max:
    return (False, False)
  
  real_max_test = args.n_interact_test_max+1
  real_max_test = min(real_max_test, len(a_list)-1)
  
  
  n = random.choice(range(args.n_interact_min,real_max))
  interactions = random.sample(a_list, k=n)
  
  n = random.choice(range(1,real_max_test))
  test = random.choices(interactions, k=n)
  train = list(set(interactions) - set(test))
  return (train, test)

def prepare_and_sample_from_kg(args, n_already_sampled, outfile_train, outfile_test):
  p = Path(args.save_dir)
  p.mkdir(parents=True, exist_ok=True)
  p = Path(p, 'distance_map.npy')
  
  kg = KnowledgeGraph()
  kg.load(args)
  logger.debug(kg)
  
  if p.exists():
    kg.load_map_and_check(p.resolve())
    # ~ print(kg.distance_map[0,:])
    # ~ print(kg.distance_map)
  else:
    kg.get_distance_map()
    # ~ print(kg.distance_map)
  
  if not p.exists():
    kg.save(p.resolve())
  
  
  hist,min_dist_nonzero, max_dist_nonzero = kg.dist_hist()
  
  # sample items from item ego-networks
  # modeling people who are rather focused on a particular topic
  min_plausible_dist = kg.get_min_plausible_dist(args.n_interact_max)
  if min_plausible_dist < 0:
    min_plausible_dist = max_dist_nonzero
  for i in range(args.n_within_range):
    only_zeros = True
    while only_zeros:
      # sample a random item
      items = kg.sample_n_items(10)
      for item in items:
        # look around the range-neighborhood of that random item. zero range doesn't make sense as there is a >= check inside
        ids = kg.get_items_in_range(item,nw_range_min=1,nw_range_max=min_plausible_dist+1)
        if len(ids) > 0:
          # and distribute items from neighborhood to train and test lists
          train, test = sample_test_train(args, list(ids))
          if train is not False and test is not False:
            only_zeros = False
            print(f"{i} {' '.join([str(j) for j in train])}", file=outfile_train)
            print(f"{i} {' '.join([str(j) for j in test])}", file=outfile_test)
            n_already_sampled += 1
            break

  # sample items from item paths
  # modeling people who are rather focused on a particular topic
  for i in range(n_already_sampled, args.n_along_path+n_already_sampled):
    only_zeros = True
    while only_zeros:
      # sample random items
      items = kg.sample_n_items(10)
      for item in items:
        path = kg.sample_path_of_len(item,args.n_interact_max, min_dist_nonzero, max_dist_nonzero, unique_path=True)
        if len(path) >= args.n_interact_min:
          # and distribute items from neighborhood to train and test lists
          train, test = sample_test_train(args, list(path))
          if train is not False and test is not False:
            only_zeros = False
            print(f"{i} {' '.join([str(j) for j in train])}", file=outfile_train)
            print(f"{i} {' '.join([str(j) for j in test])}", file=outfile_test)
            n_already_sampled += 1
            break 
  
  if args.n_rand > 0:
    # sample random items
    for i in range(n_already_sampled, args.n_rand+n_already_sampled):
      # sample random items
      items = kg.sample_n_items(args.n_interact_max)
      if len(items) > args.n_interact_min:
        train, test = sample_test_train(args, list(path))
        if train is not False and test is not False:
          only_zeros = False
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
        n_already_sampled = rp_sampler.sample_interactions(_train, _test)
      
      if args.use_kg_sampling:
        n_already_sampled = prepare_and_sample_from_kg(args, n_already_sampled, _train, _test)
  except:
    Path(args.save_dir, 'train.txt').unlink(missing_ok=True)
    Path(args.save_dir, 'test.txt').unlink(missing_ok=True)
    logger.warning(f"an error occurred. removed train.txt and test.txt")
    return
  logger.info(f"done sampling {n_already_sampled} user profiles in total")
      
              
  

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
                      
  parser.add_argument('--items_file',                                nargs='?', help='items file')
  parser.add_argument('--entities_file',                             nargs='?', help='entities file')
  parser.add_argument('--knowledge_graph_file',                      nargs='?', help='file containing knowledge graph')
  parser.add_argument('--user_file',             default=None,       nargs='?', help='file containing user ids')
  parser.add_argument('--interactions_file',     default=None,       nargs='?', help='file containing interactions of real users')
  parser.add_argument('--save_dir',              default='.',        nargs='?', help='save numpy objects to this dir')

  parser.add_argument('--n_profiles',            default=100, type=int, help='number of profiles to sample in total')
  parser.add_argument('--perc_within_range',     default= 50.0, type=float, help='percentage of profiles that will be sampled from network proximity of random items. if perc_within_range and perc_along_path do not add up to 100%, the rest will be sampled randomly')
  parser.add_argument('--perc_along_path',       default= 50.0, type=float, help='percentage of profiles that will be sampled from network paths of items. if perc_within_range and perc_along_path do not add up to 100%, the rest will be sampled randomly')

  parser.add_argument('--n_interact_max',        default=200, type=int, help='maximum number of interactions per sampled profile')
  parser.add_argument('--n_interact_min',        default= 30, type=int, help='minimal number of interactions per sampled profile')
  parser.add_argument('--n_interact_test_max',   default= 10, type=int, help='maximum number of interactions per sampled profile that go to the test set')
                                       
  args = parser.parse_args()
  
  configure_logging(args)
  
  main(args)

