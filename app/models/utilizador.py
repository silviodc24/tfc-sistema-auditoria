from app import db


class Utilizador(db.Model):
    __tablename__ = 'utilizador'

    id_utilizador = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    perfil = db.Column(db.Enum('auditor', 'administrador'),
                       nullable=False, default='auditor')
    ativo = db.Column(db.Boolean, nullable=False, default=True)

    # Relacao com auditoria
    auditorias = db.relationship('Auditoria', backref='utilizador', lazy=True)

    def __repr__(self):
        return f'<Utilizador {self.nome} — {self.perfil}>'
