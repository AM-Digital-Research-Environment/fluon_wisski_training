class TestWsgiEntrypoint:
    def test_creates_an_application(self):
        from server.wsgi import app

        assert app is not None
