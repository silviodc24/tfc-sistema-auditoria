from app import db
from datetime import datetime

class Auditoria(db.Model):
    __tablename__ = 'auditoria'

    id_auditoria            = db.Column(db.Integer, primary_key=True)
    id_utilizador           = db.Column(db.Integer, db.ForeignKey('utilizador.id_utilizador'), nullable=False)
    data_execucao           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    periodo_analisado       = db.Column(db.String(20), nullable=False)
    total_transacoes        = db.Column(db.Integer, nullable=False, default=0)
    total_nao_conformidades = db.Column(db.Integer, nullable=False, default=0)
    status                  = db.Column(db.Enum('em_curso', 'concluida', 'erro'), nullable=False, default='em_curso')

    # Relacao com auditoria_aquisicao
    avaliacoes = db.relationship('AuditoriaAquisicao', backref='auditoria', lazy=True)

    def __repr__(self):
        return f'<Auditoria {self.id_auditoria} — {self.periodo_analisado} — {self.status}>'