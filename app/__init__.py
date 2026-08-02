import secrets

from flask import Flask, current_app, flash, g, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour'],
    storage_uri='memory://',
)


def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Railway (e qualquer PaaS atras de proxy reverso) termina o TLS antes do
    # processo Gunicorn e reenvia via HTTP interno com X-Forwarded-*.
    # Sem isto, request.remote_addr e request.is_secure ficam sempre errados.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor autentique-se para aceder a esta página.'
    login_manager.login_message_category = 'warning'

    csrf.init_app(app)
    limiter.init_app(app)

    @app.before_request
    def gerar_csp_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

    @app.before_request
    def marcar_sessao_permanente():
        # Sem isto, PERMANENT_SESSION_LIFETIME e ignorado — sessoes do
        # Flask nao sao "permanentes" por omissao.
        session.permanent = True

    @app.context_processor
    def injectar_csp_nonce():
        return {'csp_nonce': g.get('csp_nonce', '')}

    @app.after_request
    def aplicar_headers_seguranca(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{g.get('csp_nonce', '')}' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "font-src 'self' https://cdn.jsdelivr.net data:; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.errorhandler(CSRFError)
    def erro_csrf(e):
        flash('O formulário expirou ou é inválido. Tente novamente.', 'warning')
        return redirect(request.referrer or url_for('main.index'))

    @app.errorhandler(429)
    def erro_rate_limit(e):
        flash('Demasiadas tentativas. Aguarde um momento antes de tentar novamente.', 'danger')
        return redirect(request.referrer or url_for('main.index')), 429

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
