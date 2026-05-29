from app import db

class CentroCusto(db.Model):
    __tablename__ = 'centro_custo'

    id_centro      = db.Column(db.Integer, primary_key=True)
    nome           = db.Column(db.String(100), nullable=False)
    departamento   = db.Column(db.String(100), nullable=False)
    id_responsavel = db.Column(db.Integer, db.ForeignKey('colaborador.id_colaborador'), nullable=False)
    ativo          = db.Column(db.Boolean, nullable=False, default=True)

    # Relacoes com orcamento e aquisicao
    orcamentos  = db.relationship('Orcamento', backref='centro', lazy=True)
    aquisicoes  = db.relationship('Aquisicao', backref='centro', lazy=True)

    def __repr__(self):
        return f'<CentroCusto {self.nome}>'