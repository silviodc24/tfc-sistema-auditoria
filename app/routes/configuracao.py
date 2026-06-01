from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.regra_auditoria import RegraAuditoria
from app.models.limiar_autorizacao import LimiarAutorizacao

config_bp = Blueprint('configuracao', __name__, url_prefix='/configuracao')


@config_bp.route('/')
def index():
    """Lista todas as regras de auditoria."""
    regras = RegraAuditoria.query.order_by(RegraAuditoria.codigo).all()
    return render_template('configuracao/index.html', regras=regras)


@config_bp.route('/regras/<int:id>/toggle', methods=['POST'])
def toggle_regra(id):
    """Activa ou desactiva uma regra de auditoria."""
    regra = RegraAuditoria.query.get_or_404(id)
    regra.ativa = not regra.ativa
    db.session.commit()
    estado = 'activada' if regra.ativa else 'desactivada'
    flash(f'Regra {regra.codigo} {estado} com sucesso.', 'success')
    return redirect(url_for('configuracao.index'))


@config_bp.route('/regras/<int:id>/editar', methods=['GET', 'POST'])
def editar_regra(id):
    """Edita o valor_referencia de uma regra de auditoria."""
    regra = RegraAuditoria.query.get_or_404(id)

    if request.method == 'POST':
        valor = request.form.get('valor_referencia')
        regra.valor_referencia = float(valor) if valor else None
        db.session.commit()
        flash(f'Regra {regra.codigo} actualizada com sucesso.', 'success')
        return redirect(url_for('configuracao.index'))

    return render_template('configuracao/editar_regra.html', regra=regra)


@config_bp.route('/limiares')
def limiares():
    """Lista os limiares de autorizacao."""
    limiares = LimiarAutorizacao.query.order_by(
        LimiarAutorizacao.valor_minimo
    ).all()
    return render_template('configuracao/limiares.html', limiares=limiares)


@config_bp.route('/limiares/<int:id>/editar', methods=['GET', 'POST'])
def editar_limiar(id):
    """Edita um limiar de autorizacao."""
    limiar = LimiarAutorizacao.query.get_or_404(id)

    if request.method == 'POST':
        limiar.valor_minimo = float(request.form.get('valor_minimo'))
        valor_maximo = request.form.get('valor_maximo')
        limiar.valor_maximo = float(valor_maximo) if valor_maximo else None
        limiar.nivel_minimo = int(request.form.get('nivel_minimo'))
        db.session.commit()
        flash('Limiar actualizado com sucesso.', 'success')
        return redirect(url_for('configuracao.limiares'))

    return render_template('configuracao/editar_limiar.html', limiar=limiar)