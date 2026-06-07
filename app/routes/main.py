from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.auditoria import Auditoria
from app.models.auditoria_aquisicao import AuditoriaAquisicao
from app.models.nao_conformidade import NaoConformidade
from app.models.centro_custo import CentroCusto
from app import db

main = Blueprint('main', __name__)


@main.route('/')
@login_required
def index():
    # Indicadores gerais
    total_auditorias = Auditoria.query.count()
    total_conformes = AuditoriaAquisicao.query.filter_by(resultado='conforme').count()
    total_nao_conformes = AuditoriaAquisicao.query.filter_by(resultado='nao_conforme').count()
    total_criticas = NaoConformidade.query.filter_by(gravidade='critica').count()

    # Ultimas auditorias
    ultimas_auditorias = Auditoria.query.order_by(
        Auditoria.data_execucao.desc()
    ).limit(5).all()

    # Ultimas nao conformidades
    ultimas_nao_conformidades = NaoConformidade.query.order_by(
        NaoConformidade.data_registo.desc()
    ).limit(8).all()

    # Dados para grafico de barras — conformes vs nao conformes por centro de custo
    centros = CentroCusto.query.filter_by(ativo=True).all()
    labels_centros = []
    dados_conformes = []
    dados_nao_conformes = []

    for centro in centros:
        labels_centros.append(centro.departamento)
        conformes = db.session.query(AuditoriaAquisicao).join(
            AuditoriaAquisicao.aquisicao
        ).filter(
            AuditoriaAquisicao.resultado == 'conforme',
            db.text(f'aquisicao.id_centro = {centro.id_centro}')
        ).count()
        nao_conformes = db.session.query(AuditoriaAquisicao).join(
            AuditoriaAquisicao.aquisicao
        ).filter(
            AuditoriaAquisicao.resultado == 'nao_conforme',
            db.text(f'aquisicao.id_centro = {centro.id_centro}')
        ).count()
        dados_conformes.append(conformes)
        dados_nao_conformes.append(nao_conformes)

    # Dados para grafico de rosca — distribuicao de gravidades
    total_baixa = NaoConformidade.query.filter_by(gravidade='baixa').count()
    total_media = NaoConformidade.query.filter_by(gravidade='media').count()
    total_alta = NaoConformidade.query.filter_by(gravidade='alta').count()
    total_critica = NaoConformidade.query.filter_by(gravidade='critica').count()

    return render_template('index.html',
        total_auditorias=total_auditorias,
        total_conformes=total_conformes,
        total_nao_conformes=total_nao_conformes,
        total_criticas=total_criticas,
        ultimas_auditorias=ultimas_auditorias,
        ultimas_nao_conformidades=ultimas_nao_conformidades,
        labels_centros=labels_centros,
        dados_conformes=dados_conformes,
        dados_nao_conformes=dados_nao_conformes,
        total_baixa=total_baixa,
        total_media=total_media,
        total_alta=total_alta,
        total_critica=total_critica
    )