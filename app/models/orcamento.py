from app import db

class Orcamento(db.Model):
    __tablename__ = 'orcamento'

    id_orcamento    = db.Column(db.Integer, primary_key=True)
    id_centro       = db.Column(db.Integer, db.ForeignKey('centro_custo.id_centro'), nullable=False)
    periodo         = db.Column(db.String(20), nullable=False)
    valor_orcado    = db.Column(db.Numeric(15, 2), nullable=False)
    valor_executado = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)

    # Relacao com aquisicao
    aquisicoes = db.relationship('Aquisicao', backref='orcamento', lazy=True)

    def __repr__(self):
        return f'<Orcamento {self.periodo} — Centro {self.id_centro}>'