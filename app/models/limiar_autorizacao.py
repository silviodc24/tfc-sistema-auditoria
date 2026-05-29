from app import db

class LimiarAutorizacao(db.Model):
    __tablename__ = 'limiar_autorizacao'

    id_limiar    = db.Column(db.Integer, primary_key=True)
    id_regra     = db.Column(db.Integer, db.ForeignKey('regra_auditoria.id_regra'), nullable=False)
    valor_minimo = db.Column(db.Numeric(15, 2), nullable=False)
    valor_maximo = db.Column(db.Numeric(15, 2), nullable=True)
    nivel_minimo = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<LimiarAutorizacao Regra {self.id_regra} — Nivel {self.nivel_minimo}>'