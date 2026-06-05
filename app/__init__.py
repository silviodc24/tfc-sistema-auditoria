from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor autentique-se para aceder a esta página.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.utilizador import Utilizador
        return Utilizador.query.get(int(user_id))

    from app.routes.main import main
    app.register_blueprint(main)

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.auditoria import auditoria_bp
    app.register_blueprint(auditoria_bp)

    from app.routes.aquisicao import aquisicao_bp
    app.register_blueprint(aquisicao_bp)

    from app.routes.nao_conformidade import nc_bp
    app.register_blueprint(nc_bp)

    from app.routes.configuracao import config_bp
    app.register_blueprint(config_bp)

    from app import models

    return app
