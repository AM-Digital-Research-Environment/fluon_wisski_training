#!/usr/bin/env python3

import logging
from pathlib import Path

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
    # ~ print(kg.distance_map[0,:])
    # ~ print(kg.distance_map)
  else:
    kg.get_distance_map()
    # ~ print(kg.distance_map)

if __name__ == '__main__':
  
  parser = get_preconfigured_parser()
  args = parser.parse_args()
  configure_logging(args, BASE)
  
  main(args)

