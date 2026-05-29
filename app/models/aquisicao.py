from app import db

class Aquisicao(db.Model):
    __tablename__ = 'aquisicao'

    id_aquisicao         = db.Column(db.Integer, primary_key=True)
    id_centro            = db.Column(db.Integer, db.ForeignKey('centro_custo.id_centro'), nullable=False)
    id_orcamento         = db.Column(db.Integer, db.ForeignKey('orcamento.id_orcamento'), nullable=False)
    id_solicitante       = db.Column(db.Integer, db.ForeignKey('colaborador.id_colaborador'), nullable=False)
    id_aprovador         = db.Column(db.Integer, db.ForeignKey('colaborador.id_colaborador'), nullable=False)
    data_solicitacao     = db.Column(db.Date, nullable=False)
    data_aprovacao       = db.Column(db.Date, nullable=True)
    valor                = db.Column(db.Numeric(15, 2), nullable=False)
    descricao            = db.Column(db.String(255), nullable=False)
    tipo_aquisicao       = db.Column(db.Enum('bem', 'servico'), nullable=False)
    documento_referencia = db.Column(db.String(100), nullable=True)
    status_aprovacao     = db.Column(db.Enum('aprovado', 'pendente', 'rejeitado'), nullable=False, default='pendente')
    origem_dado          = db.Column(db.Enum('csv', 'erp', 'manual'), nullable=False, default='csv')
    confirmacao_recepcao = db.Column(db.Boolean, nullable=False, default=False)

    # Relacao com auditoria_aquisicao
    avaliacoes = db.relationship('AuditoriaAquisicao', backref='aquisicao', lazy=True)

    def __repr__(self):
        return f'<Aquisicao {self.id_aquisicao} — {self.valor} Kz>'