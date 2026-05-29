from app import db
from datetime import datetime

class NaoConformidade(db.Model):
    __tablename__ = 'nao_conformidade'

    id_nao_conformidade    = db.Column(db.Integer, primary_key=True)
    id_auditoria_aquisicao = db.Column(db.Integer, db.ForeignKey('auditoria_aquisicao.id_auditoria_aquisicao'), nullable=False)
    id_regra               = db.Column(db.Integer, db.ForeignKey('regra_auditoria.id_regra'), nullable=False)
    descricao              = db.Column(db.Text, nullable=False)
    gravidade              = db.Column(db.Enum('baixa', 'media', 'alta', 'critica'), nullable=False)
    data_registo           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status                 = db.Column(db.Enum('aberta', 'em_analise', 'resolvida', 'ignorada'), nullable=False, default='aberta')
    comentario_auditor     = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<NaoConformidade {self.id_nao_conformidade} — {self.gravidade} — {self.status}>'