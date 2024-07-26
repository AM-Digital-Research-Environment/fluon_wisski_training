from flask import Blueprint
from flask_restx import Api

from .api.v1 import api as v1

bp = Blueprint("api", __name__, url_prefix="/api/v1")
api = Api(bp, title="APIv1", version="1.0")

api.add_namespace(v1)
