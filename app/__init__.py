# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash
import os

socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///app.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    from . import routes, sockets, models
    app.register_blueprint(routes.bp)
    sockets.init_socketio(socketio)

    with app.app_context():
        db.create_all()

        # ✅ Create default admin user if not exists
        if not models.User.query.filter_by(username="admin").first():
            admin = models.User(
                username="admin",
                password=generate_password_hash("password"),
                is_admin=True,
                email='admin@example.com'
            )
            db.session.add(admin)
            db.session.commit()

    return app

