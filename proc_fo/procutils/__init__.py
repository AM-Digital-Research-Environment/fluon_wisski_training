import logging
from pathlib import Path
import argparse
import random

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


def get_log_filename(out_dir, base, ext='.log'):
  def get_basename(log_id, base, ext='.log'):
    return '{}_{:d}{}'.format(base,log_id,ext)
  
  log_count = 0
  f = Path(out_dir, get_basename(log_count, base))
  while f.exists():
    log_count += 1
    f = Path(out_dir, get_basename(log_count, base))
  return f.resolve()


def configure_logging(args, base):
  if args.log_to_file:
    p = Path(args.log_dir)
    p.mkdir(parents=True, exist_ok=True)
  for handler in logging.root.handlers:
    logging.root.removeHandler(handler)
  logging.root.handlers = []
  logging.root.setLevel(args.log_level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  
  if args.log_to_file:
    logfile = logging.FileHandler(get_log_filename(args.log_dir, base=base))
    logfile.setFormatter(formatter)
    logging.root.addHandler(logfile)

  if not args.log_to_console_off:
    logconsole = logging.StreamHandler()
    logconsole.setFormatter(formatter)
    logging.root.addHandler(logconsole)


def get_preconfigured_parser():
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
  
  return parser
