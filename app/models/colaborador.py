from app import db

class Colaborador(db.Model):
    __tablename__ = 'colaborador'

    id_colaborador    = db.Column(db.Integer, primary_key=True)
    nome              = db.Column(db.String(100), nullable=False)
    email             = db.Column(db.String(150), nullable=False, unique=True)
    nivel_hierarquico = db.Column(db.Integer, nullable=False)
    ativo             = db.Column(db.Boolean, nullable=False, default=True)

    # Relacoes com centro_custo e aquisicao
    centros_responsavel  = db.relationship('CentroCusto', backref='responsavel', lazy=True, foreign_keys='CentroCusto.id_responsavel')
    aquisicoes_solicitante = db.relationship('Aquisicao', backref='solicitante', lazy=True, foreign_keys='Aquisicao.id_solicitante')
    aquisicoes_aprovador   = db.relationship('Aquisicao', backref='aprovador', lazy=True, foreign_keys='Aquisicao.id_aprovador')

    def __repr__(self):
        return f'<Colaborador {self.nome} — Nivel {self.nivel_hierarquico}>'