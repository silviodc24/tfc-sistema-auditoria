import os
from datetime import timedelta


SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY não definida. Defina a variável de ambiente SECRET_KEY '
        '(ficheiro .env) antes de iniciar a aplicação — necessária para '
        'sessões, CSRF e cookies seguros.'
    )


class Config:
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').strip().lower() in ('1', 'true', 'yes', 'on')

    # Cookies de sessao e CSRF. SECURE fica ligado a DEBUG porque em
    # desenvolvimento local (http://localhost) o browser descarta cookies
    # marcados Secure — so faz sentido exigir HTTPS quando DEBUG=False.
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=15)

    WTF_CSRF_SSL_STRICT = not DEBUG

    # Limite de tamanho de upload (rotas de importacao em configuracao.py
    # leem o ficheiro inteiro para memoria sem limite proprio).
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
