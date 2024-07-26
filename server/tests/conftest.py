from flask import Flask
from flask.testing import FlaskClient
import pytest
import pathlib
from server import create_app


@pytest.fixture()
def cluster_file(tmp_path: pathlib.Path):
    dir = tmp_path / "wisski"
    dir.mkdir()

    cluster_file = dir / "cluster.csv"
    lines = ["cluster,id,rank", "1,1,1"]
    with open(cluster_file, "w") as f:
        f.writelines(lines)

    recommendations_file = dir / "recommendations.csv"
    lines = ["user,item,rank", "1,1,1"]
    with open(recommendations_file, "w") as f:
        f.writelines(lines)

    # NOTE: no need to clean up, pytest handles this for the tmp_path fixture
    return tmp_path


@pytest.fixture()
def app(cluster_file: pathlib.Path) -> Flask:
    app = create_app(
        {"TESTING": True, "PUB_DIR": str(cluster_file), "DATA_SUBSETS": "wisski|other"}
    )

    return app


@pytest.fixture()
def client(app) -> FlaskClient:
    return app.test_client()
