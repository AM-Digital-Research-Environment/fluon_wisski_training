#!/usr/bin/env python3

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from graph import KnowledgeGraph
from utils import *

BASE = Path(__file__).stem
logger = logging.getLogger(BASE)

def main(args):
  logger.info(args)
  kg = KnowledgeGraph(args)
  kg.load(args)
  
  p = kg.get_distance_map_path()
  
  if p.exists():
    kg.load_map_and_check(p.resolve())
  else:
    kg.get_distance_map()
    kg.save(p.resolve())
  
  # load user_interactions.tsv
  logger.info(args.interactions_file)
  data = pd.read_csv(args.interactions_file, sep='\t')
  print(data)
  
  # ultimate goal:
  ## find items that are often interacted on across users
  #### tally user_interactions.tsv 2 | sort -k 1 -r | head
  ## among those items identify those that are not yet connected in the ontology or that have a very long distance
  
  
if __name__ == '__main__':
  parser = get_preconfigured_parser()
  args = parser.parse_args()
  
  if args.interactions_file is None:
    raise Exception("Need the interactions_file to work with!")
  
  configure_logging(args, BASE)
  
  main(args)

