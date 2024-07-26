from flask import Flask


def conf_is_set(app: Flask, key: str) -> bool:
    if key not in app.config or app.config[key] is None:
        return False
    return True


def create_app(test_config: dict | None = None):
    app = Flask(__name__)
    app.config.from_object("server.default_settings")

    if test_config is None:
        app.config.from_envvar("FO_SERVER_SETTINGS", silent=True)
    else:
        app.config.from_mapping(test_config)

    if not conf_is_set(app, "PUB_DIR"):
        app.logger.critical("PUB_DIR not set.")
        return

    if (
        not conf_is_set(app, "DATA_SUBSETS")
        or len(app.config["DATA_SUBSETS"].split("|")) == 0
    ):
        app.logger.critical(
            "No data files provided in config. Have you set DATA_SUBSETS?"
        )
        return

    app.config["DATA_SUBSETS"] = app.config["DATA_SUBSETS"].split("|")

    from .apiv1 import bp as apiv1

    app.register_blueprint(apiv1)

    return app
