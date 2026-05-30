from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.auditoria import Auditoria
from app.models.utilizador import Utilizador
from app.services.motor_auditoria import executar_auditoria

auditoria_bp = Blueprint('auditoria', __name__, url_prefix='/auditoria')


@auditoria_bp.route('/')
def index():
    """Lista todas as sessoes de auditoria."""
    auditorias = Auditoria.query.order_by(Auditoria.data_execucao.desc()).all()
    return render_template('auditoria/index.html', auditorias=auditorias)


@auditoria_bp.route('/nova', methods=['GET', 'POST'])
def nova():
    """Cria e executa uma nova sessao de auditoria."""
    utilizadores = Utilizador.query.filter_by(ativo=True).all()

    if request.method == 'POST':
        id_utilizador = request.form.get('id_utilizador')
        periodo = request.form.get('periodo')

        if not id_utilizador or not periodo:
            flash('Preencha todos os campos.', 'danger')
            return render_template('auditoria/nova.html', utilizadores=utilizadores)

        # Cria a sessao de auditoria
        auditoria = Auditoria(
            id_utilizador=id_utilizador,
            periodo_analisado=periodo,
            status='em_curso'
        )
        db.session.add(auditoria)
        db.session.flush()

        # Executa o motor de regras
        sucesso, mensagem = executar_auditoria(auditoria, periodo)

        if sucesso:
            flash(f'Auditoria concluida. {mensagem}', 'success')
            return redirect(url_for('auditoria.detalhe', id=auditoria.id_auditoria))
        else:
            flash(f'Erro na auditoria: {mensagem}', 'danger')
            return render_template('auditoria/nova.html', utilizadores=utilizadores)

    return render_template('auditoria/nova.html', utilizadores=utilizadores)


@auditoria_bp.route('/<int:id>')
def detalhe(id):
    """Mostra o detalhe de uma sessao de auditoria."""
    auditoria = Auditoria.query.get_or_404(id)
    return render_template('auditoria/detalhe.html', auditoria=auditoria)
