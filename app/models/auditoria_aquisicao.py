from app import db

class AuditoriaAquisicao(db.Model):
    __tablename__ = 'auditoria_aquisicao'

    id_auditoria_aquisicao = db.Column(db.Integer, primary_key=True)
    id_auditoria           = db.Column(db.Integer, db.ForeignKey('auditoria.id_auditoria'), nullable=False)
    id_aquisicao           = db.Column(db.Integer, db.ForeignKey('aquisicao.id_aquisicao'), nullable=False)
    resultado              = db.Column(db.Enum('conforme', 'nao_conforme', 'inconclusivo'), nullable=False)

    # Relacao com nao_conformidade
    nao_conformidades = db.relationship('NaoConformidade', backref='auditoria_aquisicao', lazy=True)

    def __repr__(self):
        return f'<AuditoriaAquisicao Auditoria {self.id_auditoria} — Aquisicao {self.id_aquisicao} — {self.resultado}>'