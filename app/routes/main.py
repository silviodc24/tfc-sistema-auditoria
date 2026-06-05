from flask import Blueprint, render_template
from app.models.auditoria import Auditoria
from app.models.auditoria_aquisicao import AuditoriaAquisicao
from app.models.nao_conformidade import NaoConformidade
from flask_login import login_required

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def index():
    total_auditorias = Auditoria.query.count()
    total_conformes = AuditoriaAquisicao.query.filter_by(
        resultado='conforme').count()
    total_nao_conformes = AuditoriaAquisicao.query.filter_by(
        resultado='nao_conforme').count()
    total_criticas = NaoConformidade.query.filter_by(
        gravidade='critica').count()
    ultimas_auditorias = Auditoria.query.order_by(
        Auditoria.data_execucao.desc()).limit(5).all()
    ultimas_nao_conformidades = NaoConformidade.query.order_by(
        NaoConformidade.data_registo.desc()).limit(8).all()

    return render_template('index.html',
                           total_auditorias=total_auditorias,
                           total_conformes=total_conformes,
                           total_nao_conformes=total_nao_conformes,
                           total_criticas=total_criticas,
                           ultimas_auditorias=ultimas_auditorias,
                           ultimas_nao_conformidades=ultimas_nao_conformidades
                           )
