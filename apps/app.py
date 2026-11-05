from pathlib import Path
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="2AZSMss3p5QPbcY2hBsj",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{Path(__file__).parent.parent / 'local.sqlite'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ECHO=True,
    )
    db.init_app(app)
    Migrate(app, db)

    from apps.home.views import home
    from apps.register.views import register_bp
    from apps.login.views import login_bp

    app.register_blueprint(home)
    app.register_blueprint(register_bp)
    app.register_blueprint(login_bp)

    return app
