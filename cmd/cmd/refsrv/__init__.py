import random
from pathlib import Path

import logging

BASE = Path(__file__).parent.stem
logger = logging.getLogger(BASE)


class RefSrvSampler:

    def __init__(
        self,
        interactions_file: Path,
        user_file: Path,
        items_file: Path,
        n_interact_max: int,
        n_interact_test_max: int,
    ):
        self.interactions_file = interactions_file
        self.user_file = user_file
        self.items_file = items_file
        self.n_interact_max = n_interact_max
        self.n_interact_test_max = n_interact_test_max
        self.u_ids: dict[int, str] = self.load_user_file()

    @property
    def n_known_users(self) -> int:
        return len(self.u_ids)

    def load_user_file(self):
        out = {}
        with open(self.user_file) as _uf:
            next(_uf)
            for i, line in enumerate(_uf):
                fields = line.strip().split("\t")
                out[int(fields[0])] = i
        return out

    def sample_interactions(self, outfile_train, outfile_test):
        i_ids = {}
        with open(self.items_file) as _i:
            next(_i)
            for line in _i:
                fields = line.strip().split(" ")
                _id = int(fields[2])
                i_ids[_id] = int(fields[0])
        n_known_items = len(i_ids)
        assert self.n_interact_max <= n_known_items

        interactions = {}
        with open(self.interactions_file) as _i:
            next(_i)
            u_interactions = []
            last_u = None
            for line in _i:
                fields = line.strip().split("\t")
                user = int(fields[0])
                item = int(fields[1])
                if last_u is None:
                    last_u = user
                if last_u != user:
                    interactions[self.u_ids[last_u]] = u_interactions
                    u_interactions = []
                    last_u = user
                u_interactions.append(i_ids[item])
            interactions[self.u_ids[user]] = u_interactions

        n_sampled = 0
        for u in range(self.n_known_users):
            if u in interactions:
                n = random.choice(
                    range(
                        1,
                        min(self.n_interact_test_max + 1, len(interactions[u]) - 1),
                    )
                )  # user interactions might be fewer. but we need data for testing nevertheless
                test = random.choices(interactions[u], k=n)
                train = list(set(interactions[u]) - set(test))
                # TODO: collect lines, then write in batches
                print(u, " ".join(str(i) for i in test), file=outfile_test)
                print(u, " ".join(str(i) for i in train), file=outfile_train)
                n_sampled += 1
        return n_sampled
