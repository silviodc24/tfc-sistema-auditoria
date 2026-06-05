from flask import Blueprint, render_template, request
from app.models.aquisicao import Aquisicao
from app.models.centro_custo import CentroCusto
from app.models.orcamento import Orcamento
from flask_login import login_required

aquisicao_bp = Blueprint('aquisicao', __name__, url_prefix='/aquisicoes')


@aquisicao_bp.route('/')
@login_required
def index():
    """Lista todas as aquisicoes com filtros opcionais."""
    id_centro = request.args.get('id_centro', '')
    periodo = request.args.get('periodo', '')
    status = request.args.get('status', '')

    query = Aquisicao.query

    if id_centro:
        query = query.filter_by(id_centro=id_centro)

    if periodo:
        query = query.join(Orcamento).filter(Orcamento.periodo == periodo)

    if status:
        query = query.filter_by(status_aprovacao=status)

    aquisicoes = query.order_by(Aquisicao.data_solicitacao.asc()).all()
    centros = CentroCusto.query.filter_by(ativo=True).all()
    orcamentos = Orcamento.query.order_by(Orcamento.periodo).all()

    return render_template('aquisicao/index.html',
        aquisicoes=aquisicoes,
        centros=centros,
        orcamentos=orcamentos,
        filtro_centro=id_centro,
        filtro_periodo=periodo,
        filtro_status=status
    )

