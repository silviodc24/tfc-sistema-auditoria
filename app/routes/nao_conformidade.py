from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.nao_conformidade import NaoConformidade
from app.models.regra_auditoria import RegraAuditoria
from flask_login import login_required

nc_bp = Blueprint('nao_conformidade', __name__, url_prefix='/nao-conformidades')


@nc_bp.route('/')
@login_required
def index():
    """Lista todas as nao conformidades com filtros opcionais."""
    gravidade = request.args.get('gravidade', '')
    status = request.args.get('status', '')
    id_regra = request.args.get('id_regra', '')

    query = NaoConformidade.query

    if gravidade:
        query = query.filter_by(gravidade=gravidade)
    if status:
        query = query.filter_by(status=status)
    if id_regra:
        query = query.filter_by(id_regra=id_regra)

    nao_conformidades = query.order_by(
        NaoConformidade.data_registo.desc()
    ).all()

    regras = RegraAuditoria.query.order_by(RegraAuditoria.codigo).all()

    return render_template('nao_conformidade/index.html',
        nao_conformidades=nao_conformidades,
        regras=regras,
        filtro_gravidade=gravidade,
        filtro_status=status,
        filtro_regra=id_regra
    )


@nc_bp.route('/<int:id>/actualizar', methods=['POST'])
@login_required
def actualizar(id):
    """Actualiza o status e comentario de uma nao conformidade."""
    nc = NaoConformidade.query.get_or_404(id)
    novo_status = request.form.get('status')
    comentario = request.form.get('comentario_auditor')

    if novo_status:
        nc.status = novo_status
    if comentario is not None:
        nc.comentario_auditor = comentario

    db.session.commit()
    flash('Não conformidade actualizada com sucesso.', 'success')
    return redirect(url_for('nao_conformidade.index'))