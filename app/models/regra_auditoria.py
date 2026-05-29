from app import db

class RegraAuditoria(db.Model):
    __tablename__ = 'regra_auditoria'

    id_regra         = db.Column(db.Integer, primary_key=True)
    codigo           = db.Column(db.String(10), nullable=False, unique=True)
    nome             = db.Column(db.String(100), nullable=False)
    descricao        = db.Column(db.Text, nullable=False)
    campo            = db.Column(db.String(80), nullable=False)
    operador         = db.Column(db.Enum('igual', 'diferente', 'maior', 'maior_igual', 'menor', 'menor_igual', 'nulo', 'nao_nulo', 'igual_campos'), nullable=False)
    valor_referencia = db.Column(db.Numeric(15, 2), nullable=True)
    tipo_regra       = db.Column(db.Enum('orcamental', 'autorizacao', 'procedimental', 'integridade'), nullable=False)
    gravidade        = db.Column(db.Enum('baixa', 'media', 'alta', 'critica'), nullable=False, default='alta')
    ativa            = db.Column(db.Boolean, nullable=False, default=True)

    # Relacoes com limiar_autorizacao e nao_conformidade
    limiares         = db.relationship('LimiarAutorizacao', backref='regra', lazy=True)
    nao_conformidades = db.relationship('NaoConformidade', backref='regra', lazy=True)

    def __repr__(self):
        return f'<RegraAuditoria {self.codigo} — {self.nome}>'