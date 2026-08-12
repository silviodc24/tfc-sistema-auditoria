from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.auditoria import Auditoria
from app.models.aquisicao import Aquisicao
from app.services.motor_auditoria import executar_auditoria
from flask import send_file
from app.services.exportacao import gerar_pdf, gerar_excel
from flask_login import login_required, current_user
from app.utils import mascarar_id, obter_por_token

auditoria_bp = Blueprint('auditoria', __name__, url_prefix='/auditoria')


@auditoria_bp.route('/')
@login_required
def index():
    """Lista todas as sessoes de auditoria."""
    if current_user.is_admin:
        flash('Acesso restrito a auditores.', 'warning')
        return redirect(url_for('main.index'))
    auditorias = Auditoria.query.order_by(Auditoria.data_execucao.desc()).all()
    return render_template('auditoria/index.html', auditorias=auditorias)

@auditoria_bp.route('/iniciar')
@login_required
def iniciar():
    """Redireciona para aquisicoes com mensagem a pedir seleccao."""
    if current_user.is_admin:
        flash('Acesso restrito a auditores.', 'warning')
        return redirect(url_for('main.index'))
    flash('Seleccione as aquisições que pretende auditar.', 'info')
    return redirect(url_for('aquisicao.index'))

@auditoria_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    if current_user.is_admin:
        flash('Acesso restrito a auditores.', 'warning')
        return redirect(url_for('main.index'))
    # Recebe os IDs seleccionados na pagina de aquisicoes
    ids_aquisicao = request.form.getlist(
        'ids_aquisicao') or request.args.getlist('ids_aquisicao')

    # Carrega as aquisicoes seleccionadas para mostrar no formulario de confirmacao
    aquisicoes_seleccionadas = []
    if ids_aquisicao:
        aquisicoes_seleccionadas = Aquisicao.query.filter(
            Aquisicao.id_aquisicao.in_(ids_aquisicao)
        ).all()

    if request.method == 'POST' and 'confirmar' in request.form:
        id_utilizador = current_user.id_utilizador
        ids_finais = request.form.getlist('ids_aquisicao')
        periodo = request.form.get('periodo', '2025')


        if not ids_finais:
            flash('Nenhuma aquisição seleccionada. Seleciona as aquisições que desejas auditar.', 'warning')
            return redirect(url_for('aquisicao.index'))

        # Cria a sessao de auditoria
        auditoria = Auditoria(
            id_utilizador=current_user.id_utilizador,
            periodo_analisado=periodo,
            status='em_curso'
        )
        db.session.add(auditoria)
        db.session.flush()

        # Executa o motor apenas com as aquisicoes seleccionadas
        sucesso, mensagem = executar_auditoria(auditoria, ids_finais)

        if sucesso:
            flash(f'Auditoria concluída com sucesso.', 'success')
            return redirect(url_for('auditoria.detalhe', token=mascarar_id(auditoria.id_auditoria, 'auditoria')))
        else:
            flash(f'Erro na auditoria: {mensagem}', 'danger')
            return render_template('auditoria/nova.html',
                                   aquisicoes_seleccionadas=aquisicoes_seleccionadas,
                                   ids_aquisicao=ids_aquisicao
                                   )

    return render_template('auditoria/nova.html',
                           aquisicoes_seleccionadas=aquisicoes_seleccionadas,
                           ids_aquisicao=ids_aquisicao
                           )



@auditoria_bp.route('/<token>/exportar/pdf')
@login_required
def exportar_pdf(token):
    """Exporta o relatorio de auditoria em PDF."""
    if current_user.is_admin:
        flash('Acesso restrito a auditores.', 'warning')
        return redirect(url_for('main.index'))
    auditoria = obter_por_token(Auditoria, token, 'auditoria')
    if auditoria is None:
        flash('Ligação inválida.', 'danger')
        return redirect(url_for('auditoria.index'))
    buffer = gerar_pdf(auditoria)
    nome_ficheiro = f"auditoria_{auditoria.id_auditoria}_{auditoria.periodo_analisado}.pdf"
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nome_ficheiro
    )


@auditoria_bp.route('/<token>/exportar/excel')
@login_required
def exportar_excel(token):
    """Exporta o relatorio de auditoria em Excel."""
    if current_user.is_admin:
        flash('Acesso restrito a auditores.', 'warning')
        return redirect(url_for('main.index'))
    auditoria = obter_por_token(Auditoria, token, 'auditoria')
    if auditoria is None:
        flash('Ligação inválida.', 'danger')
        return redirect(url_for('auditoria.index'))
    buffer = gerar_excel(auditoria)
    nome_ficheiro = f"auditoria_{auditoria.id_auditoria}_{auditoria.periodo_analisado}.xlsx"
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nome_ficheiro
    )


@auditoria_bp.route('/<token>')
@login_required
def detalhe(token):
    """Mostra o detalhe de uma sessao de auditoria."""
    if current_user.is_admin:
        flash('Acesso restrito a auditores.', 'warning')
        return redirect(url_for('main.index'))
    auditoria = obter_por_token(Auditoria, token, 'auditoria')
    if auditoria is None:
        flash('Ligação inválida.', 'danger')
        return redirect(url_for('auditoria.index'))
    return render_template('auditoria/detalhe.html', auditoria=auditoria)
