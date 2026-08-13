from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from app.models.auditoria import Auditoria
from app.models.auditoria_aquisicao import AuditoriaAquisicao
from app.models.aquisicao import Aquisicao
from app.models.nao_conformidade import NaoConformidade
from app.models.centro_custo import CentroCusto
from app import db

main = Blueprint('main', __name__)

# Estados do ciclo de vida de uma nao conformidade que ainda representam
# risco em aberto — 'resolvida' e 'ignorada' ja foram revistas e encerradas
# pelo auditor (com ou sem correccao) e nao devem inflacionar indicadores
# de risco actual.
STATUS_EM_ABERTO = ('aberta', 'em_analise')


@main.route('/')
@login_required
def index():
    total_auditorias = Auditoria.query.count()

    # Estado ACTUAL de conformidade: usa so a avaliacao mais recente de
    # cada aquisicao. Uma aquisicao corrigida e reauditada como conforme
    # nao deve continuar a contar como nao-conforme so por causa de uma
    # auditoria antiga.
    ultima_avaliacao_id = db.session.query(
        func.max(AuditoriaAquisicao.id_auditoria_aquisicao)
    ).group_by(AuditoriaAquisicao.id_aquisicao).subquery()

    total_conformes = AuditoriaAquisicao.query.filter(
        AuditoriaAquisicao.id_auditoria_aquisicao.in_(db.session.query(ultima_avaliacao_id)),
        AuditoriaAquisicao.resultado == 'conforme'
    ).count()
    total_nao_conformes = AuditoriaAquisicao.query.filter(
        AuditoriaAquisicao.id_auditoria_aquisicao.in_(db.session.query(ultima_avaliacao_id)),
        AuditoriaAquisicao.resultado == 'nao_conforme'
    ).count()

    # Ultimas auditorias
    ultimas_auditorias = Auditoria.query.order_by(
        Auditoria.data_execucao.desc()
    ).limit(5).all()

    # Ultimas nao conformidades (actividade recente — mostra tal como registada,
    # independentemente do status)
    ultimas_nao_conformidades = NaoConformidade.query.order_by(
        NaoConformidade.data_registo.desc()
    ).limit(8).all()

    # Dados para o grafico de barras — conformes vs nao conformes por centro
    # de custo, com base na avaliacao mais recente de cada aquisicao (mesmo
    # criterio de "estado actual" usado acima). Uma unica query agrupada,
    # em vez de duas queries por centro.
    resultados_por_centro = db.session.query(
        Aquisicao.id_centro,
        AuditoriaAquisicao.resultado,
        func.count(AuditoriaAquisicao.id_auditoria_aquisicao)
    ).join(
        Aquisicao, AuditoriaAquisicao.id_aquisicao == Aquisicao.id_aquisicao
    ).filter(
        AuditoriaAquisicao.id_auditoria_aquisicao.in_(db.session.query(ultima_avaliacao_id)),
        AuditoriaAquisicao.resultado.in_(('conforme', 'nao_conforme'))
    ).group_by(Aquisicao.id_centro, AuditoriaAquisicao.resultado).all()

    mapa_resultados = {}
    for id_centro, resultado, total in resultados_por_centro:
        mapa_resultados.setdefault(id_centro, {})[resultado] = total

    centros = CentroCusto.query.filter_by(ativo=True).all()
    labels_centros = []
    dados_conformes = []
    dados_nao_conformes = []
    for centro in centros:
        valores = mapa_resultados.get(centro.id_centro, {})
        labels_centros.append(centro.nome)
        dados_conformes.append(valores.get('conforme', 0))
        dados_nao_conformes.append(valores.get('nao_conforme', 0))

    # Dados para o grafico de rosca — distribuicao de gravidades EM ABERTO.
    # Uma unica query agrupada, em vez de quatro contagens separadas.
    gravidade_counts = dict(
        db.session.query(NaoConformidade.gravidade, func.count(NaoConformidade.id_nao_conformidade))
        .filter(NaoConformidade.status.in_(STATUS_EM_ABERTO))
        .group_by(NaoConformidade.gravidade)
        .all()
    )
    total_baixa = gravidade_counts.get('baixa', 0)
    total_media = gravidade_counts.get('media', 0)
    total_alta = gravidade_counts.get('alta', 0)
    total_critica = gravidade_counts.get('critica', 0)
    total_criticas = total_critica

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
