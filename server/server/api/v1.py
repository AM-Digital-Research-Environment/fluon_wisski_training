import os
import csv

from flask import abort, current_app, Response
from flask_restx import Namespace, Resource

api = Namespace("export", "Training API, version 1")


@api.route("/<string:subset>/cluster", methods=("GET",))
@api.param("subset", "The subset of data to export")
class ClusterFinal(Resource):
    def get(self, subset: str):
        if subset not in current_app.config["DATA_SUBSETS"]:
            current_app.logger.error(f"Data file {subset} not set in app config")
            abort(403, f"Data file {subset} not allowed")

        file_path = os.path.join(current_app.config["PUB_DIR"], subset, "cluster.csv")

        if not os.path.exists(file_path):
            current_app.logger.error(f"Export path {file_path} not found")
            abort(404, f"cluster-final not found for {subset}")

        data = []
        with open(file_path, "r") as f:
            reader = csv.DictReader(f, ["id", "cluster", "rank"], delimiter=",")
            for rec in reader:
                data.append(
                    {"id": rec["id"], "cluster": rec["cluster"], "rank": rec["rank"]}
                )
        return data


@api.route("/<string:subset>/recommendations", methods=("GET",))
@api.param("subset", "The subset of data to export")
class Recommendations(Resource):
    def get(self, subset: str):
        if subset not in current_app.config["DATA_SUBSETS"]:
            current_app.logger.error(f"Data file {subset} not set in app config")
            abort(403, f"Data file {subset} not allowed")

        file_path = os.path.join(
            current_app.config["PUB_DIR"], subset, "recommendations.csv"
        )

        if not os.path.exists(file_path):
            current_app.logger.error(f"Export path {file_path} not found")
            abort(404, f"cluster-final not found for {subset}")

        data = []
        with open(file_path, "r") as f:
            reader = csv.DictReader(f, ["user", "item", "rank"], delimiter=",")
            for rec in reader:
                data.append(
                    {"user": rec["user"], "item": rec["item"], "rank": rec["rank"]}
                )

        return data
