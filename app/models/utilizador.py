from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Utilizador(db.Model, UserMixin):
    __tablename__ = 'utilizador'

    id_utilizador = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False, default='')
    perfil = db.Column(db.Enum('auditor', 'administrador'),
                       nullable=False, default='auditor')
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    auditorias = db.relationship('Auditoria', backref='utilizador', lazy=True)

    def get_id(self):
        return str(self.id_utilizador)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.perfil == 'administrador'

    def __repr__(self):
        return f'<Utilizador {self.nome} — {self.perfil}>'
