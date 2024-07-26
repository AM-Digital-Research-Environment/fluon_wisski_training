from flask.testing import FlaskClient

from server import create_app


class TestClusterExportEndpointV1:
    def test_returns_Ok(self, client: FlaskClient):
        response = client.get("/api/v1/export/wisski/cluster")
        assert response.status_code == 200

    def test_returns_Forbidden_when_subset_not_registered(self, client: FlaskClient):
        response = client.get("/api/v1/export/idontexist/cluster")
        assert response.status_code == 403

    def test_returns_NotFound_when_file_does_not_exist(self, app):
        app.config.update({"PUB_DIR": "notexist"})
        client = app.test_client()
        response = client.get("/api/v1/export/wisski/cluster")
        assert response.status_code == 404


class TestRecommendationsExportEndpointV1:
    def test_returns_Ok(self, client: FlaskClient):
        response = client.get("/api/v1/export/wisski/recommendations")
        assert response.status_code == 200

    def test_returns_Forbidden_when_subset_not_registered(self, client: FlaskClient):
        response = client.get("/api/v1/export/idontexist/recommendations")
        assert response.status_code == 403

    def test_returns_NotFound_when_file_does_not_exist(self, app):
        app.config.update({"PUB_DIR": "notexist"})
        client = app.test_client()
        response = client.get("/api/v1/export/wisski/recommendations")
        assert response.status_code == 404
