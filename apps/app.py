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
    #app変更点
    from apps.situation.models import Situation
    Migrate(app, db)

    from apps.home.views import home
    from apps.register.views import register_bp
    from apps.login.views import login_bp
    from apps.chat.views import chat
    from apps.goal.views import goal
    from apps.history.views import history
    from apps.body_input.views import body_input

    from apps.friend.views import friend
    from apps.implementation.views import implementation
    from apps.registration.views import registration
    from apps.lookingback.views import lookingback
    from apps.lookingback import models
    from apps.calendar.views import calendar_bp
    from apps.situation.views import situation
    from apps.help.views import help

    
    app.register_blueprint(home)
    app.register_blueprint(register_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(chat)
    app.register_blueprint(goal)
    app.register_blueprint(history)
    app.register_blueprint(body_input)


    app.register_blueprint(friend)
    app.register_blueprint(implementation)
    app.register_blueprint(registration)
    app.register_blueprint(lookingback)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(situation)
    app.register_blueprint(help)
    
    return app
