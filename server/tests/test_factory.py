from server import create_app, conf_is_set


class TestFlaskApplicationFactory:

    def test_passes_configuration_to_app(self):
        app = create_app({"TESTING": True})
        assert conf_is_set(app, "TESTING")
        assert not conf_is_set(app, "I_DONT_EXIST")

    def test_can_put_app_in_testing_mode(self):
        assert not create_app().testing
        assert create_app({"TESTING": True}).testing

    def test_does_not_create_app_if_no_publication_directory_is_configured(self):
        assert not create_app({"PUB_DIR": None})

    def test_does_not_create_app_if_no_subsets_are_configured(self):
        assert not create_app({"DATA_SUBSETS": None})
