import os


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
