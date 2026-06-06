from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.regra_auditoria import RegraAuditoria
from app.models.limiar_autorizacao import LimiarAutorizacao
from app.models.utilizador import Utilizador

config_bp = Blueprint('configuracao', __name__, url_prefix='/configuracao')


def admin_required():
    if not current_user.is_admin:
        flash('Acesso restrito a administradores.', 'danger')
        return False
    return True


# =============================================================================
# HUB DE CONFIGURACAO
# =============================================================================

@config_bp.route('/')
@login_required
def index():
    """Hub principal de configuracao."""
    return render_template('configuracao/index.html')


# =============================================================================
# GESTAO DE REGRAS
# =============================================================================

@config_bp.route('/regras')
@login_required
def regras():
    """Lista todas as regras de auditoria."""
    todas_regras = RegraAuditoria.query.order_by(RegraAuditoria.codigo).all()
    return render_template('configuracao/regras.html', regras=todas_regras)


@config_bp.route('/regras/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_regra(id):
    if not admin_required():
        return redirect(url_for('configuracao.regras'))
    regra = RegraAuditoria.query.get_or_404(id)
    regra.ativa = not regra.ativa
    db.session.commit()
    estado = 'activada' if regra.ativa else 'desactivada'
    flash(f'Regra {regra.codigo} {estado} com sucesso.', 'success')
    return redirect(url_for('configuracao.regras'))


@config_bp.route('/regras/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_regra(id):
    if not admin_required():
        return redirect(url_for('configuracao.regras'))
    regra = RegraAuditoria.query.get_or_404(id)
    if request.method == 'POST':
        valor = request.form.get('valor_referencia')
        regra.valor_referencia = float(valor) if valor else None
        db.session.commit()
        flash(f'Regra {regra.codigo} actualizada com sucesso.', 'success')
        return redirect(url_for('configuracao.regras'))
    return render_template('configuracao/editar_regra.html', regra=regra)


@config_bp.route('/limiares')
@login_required
def limiares():
    if not admin_required():
        return redirect(url_for('configuracao.regras'))
    todos_limiares = LimiarAutorizacao.query.order_by(
        LimiarAutorizacao.valor_minimo
    ).all()
    return render_template('configuracao/limiares.html', limiares=todos_limiares)


@config_bp.route('/limiares/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_limiar(id):
    if not admin_required():
        return redirect(url_for('configuracao.regras'))
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


# =============================================================================
# GESTAO DE UTILIZADORES
# =============================================================================

@config_bp.route('/utilizadores')
@login_required
def utilizadores():
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    todos = Utilizador.query.order_by(Utilizador.nome).all()
    return render_template('configuracao/utilizadores.html', utilizadores=todos)


@config_bp.route('/utilizadores/novo', methods=['GET', 'POST'])
@login_required
def novo_utilizador():
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        perfil = request.form.get('perfil')
        password = request.form.get('password')

        if Utilizador.query.filter_by(email=email).first():
            flash('Já existe um utilizador com este email.', 'danger')
            return render_template('configuracao/novo_utilizador.html')

        u = Utilizador(nome=nome, email=email, perfil=perfil)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        flash(f'Utilizador {nome} criado com sucesso.', 'success')
        return redirect(url_for('configuracao.utilizadores'))

    return render_template('configuracao/novo_utilizador.html')


@config_bp.route('/utilizadores/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_utilizador(id):
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    u = Utilizador.query.get_or_404(id)
    if u.id_utilizador == current_user.id_utilizador:
        flash('Não pode desactivar a sua própria conta.', 'danger')
        return redirect(url_for('configuracao.utilizadores'))
    u.ativo = not u.ativo
    db.session.commit()
    estado = 'activado' if u.ativo else 'desactivado'
    flash(f'Utilizador {u.nome} {estado} com sucesso.', 'success')
    return redirect(url_for('configuracao.utilizadores'))


# =============================================================================
# IMPORTACAO DE DADOS
# =============================================================================

@config_bp.route('/importacao')
@login_required
def importacao():
    """Hub de importacao de dados."""
    return render_template('configuracao/importacao.html')