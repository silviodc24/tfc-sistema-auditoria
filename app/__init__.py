from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    from app.routes.main import main
    app.register_blueprint(main)

    from app.routes.auditoria import auditoria_bp
    app.register_blueprint(auditoria_bp)

    from app.routes.aquisicao import aquisicao_bp
    app.register_blueprint(aquisicao_bp)

    from app.routes.nao_conformidade import nc_bp
    app.register_blueprint(nc_bp)

    from app import models

    return app
