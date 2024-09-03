#!/usr/bin/env python3

import csv
import logging
import random
from pathlib import Path

BASE = Path(__file__).parent.stem
logger = logging.getLogger(BASE)


class RefSrvSampler:

    def __init__(self, args):
        self.args = args
        assert self.args.interactions_file is not None
        assert self.args.user_file is not None
        self.u_ids = self.load_user_file()
        self.n_known_users = len(self.u_ids)

    def load_user_file(self):
        out: dict[str, int] = {}
        with open(self.args.user_file) as f:
            reader = csv.DictReader(
                f, fieldnames=["wisski_id", "first_seen"], delimiter="\t"
            )
            next(reader)
            for i, record in enumerate(reader):
                out[record["wisski_id"]] = i

        return out

    def sample_interactions(self, outfile_train, outfile_test):
        assert self.args.interactions_file is not None
        assert self.args.user_file is not None

        wisski_to_id: dict[str, int] = {}
        with open(self.args.items_file) as f:
            reader = csv.DictReader(
                f, fieldnames=["id", "entity", "wisskiid"], delimiter=" "
            )
            next(reader)
            for record in reader:
                wisski_to_id[record["wisskiid"]] = int(record["id"])

        n_known_items = len(wisski_to_id)
        assert self.args.n_interact_max <= n_known_items

        from pprint import pprint

        pprint(wisski_to_id)

        from collections import defaultdict

        # interactions = {}
        interactions: dict[int, set[int]] = defaultdict(set)
        with open(self.args.interactions_file) as f:
            reader = csv.DictReader(
                f, fieldnames=["wisski_user", "wisski_item", "at"], delimiter="\t"
            )
            next(f)
            u_interactions = []
            last_u = None
            for record in reader:
                user = record["wisski_user"]
                item = record["wisski_item"]
                if item in wisski_to_id:
                    interactions[self.u_ids[user]].add(wisski_to_id[item])
                # if last_u is None:
                #     last_u = user
                # if last_u != user:
                #     interactions[self.u_ids[last_u]] = u_interactions
                #     u_interactions = []
                #     last_u = user
                # u_interactions.append(wisski_to_id[item])

            #     if item in wisski_to_id:
            #         u_interactions.append(wisski_to_id[item])

            # interactions[self.u_ids[user]] = u_interactions

        pprint(interactions)
        n_sampled = 0
        for u in range(self.n_known_users):
            # INVARIANT: length of user interactions must at least 3, else we
            # choose from an empty sequence below:
            #
            # if x==1: choice(range(1, min(11, x-1))) == choice(range(1,0)) == choice([])
            # if x==2: choice(range(1, min(11, x-1))) == choice(range(1,1)) == choice([])
            # if x==3: choice(range(1, min(11, x-1))) == choice(range(1,2)) == choice([1])
            if u in interactions and len(interactions[u]) > 2:
                n = random.choice(
                    range(
                        1,
                        min(
                            self.args.n_interact_test_max + 1, len(interactions[u]) - 1
                        ),
                    )
                )  # user interactions might be fewer. but we need data for testing nevertheless
                test = random.choices(list(interactions[u]), k=n)
                train = list(set(interactions[u]) - set(test))
                print(u, " ".join(str(i) for i in test), file=outfile_test)
                print(u, " ".join(str(i) for i in train), file=outfile_train)
                n_sampled += 1
        return n_sampled
