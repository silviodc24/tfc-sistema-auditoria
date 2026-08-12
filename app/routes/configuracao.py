import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.regra_auditoria import RegraAuditoria
from app.models.limiar_autorizacao import LimiarAutorizacao
from app.models.utilizador import Utilizador
from flask import send_file
from app.services.importacao import (
    importar_colaboradores,
    importar_centros_custo,
    importar_orcamentos,
    importar_aquisicoes
)

config_bp = Blueprint('configuracao', __name__, url_prefix='/configuracao')

DOMINIO_EMAIL_PERMITIDO = '@ns-aplicacao.ao'


def validar_politica_password(password, nome='', email=''):
    """Valida a password contra a politica minima do sistema.
    Devolve (True, None) se valida, (False, mensagem) caso contrario.
    """
    if len(password) < 10:
        return False, 'A password deve ter pelo menos 10 caracteres.'
    if not re.search(r'[A-Z]', password):
        return False, 'A password deve conter pelo menos uma letra maiúscula.'
    if not re.search(r'[a-z]', password):
        return False, 'A password deve conter pelo menos uma letra minúscula.'
    if not re.search(r'[0-9]', password):
        return False, 'A password deve conter pelo menos um dígito.'
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, 'A password deve conter pelo menos um caracter especial.'

    password_lower = password.lower()
    partes_triviais = [p.lower() for p in nome.split() if len(p) >= 4]
    if email:
        partes_triviais.append(email.split('@')[0].lower())
    if any(parte in password_lower for parte in partes_triviais if parte):
        return False, 'A password não pode conter o nome ou o email do utilizador.'

    return True, None


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

        gravidade = request.form.get('gravidade')
        if gravidade not in ('baixa', 'media', 'alta', 'critica'):
            flash('Gravidade inválida.', 'danger')
            return render_template('configuracao/editar_regra.html', regra=regra)
        regra.gravidade = gravidade

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
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        perfil = request.form.get('perfil')
        password = request.form.get('password')

        if not email.endswith(DOMINIO_EMAIL_PERMITIDO):
            flash(f'O email tem de pertencer ao domínio "{DOMINIO_EMAIL_PERMITIDO}".', 'danger')
            return render_template('configuracao/novo_utilizador.html',
                                    nome=nome, email=email, perfil=perfil)

        if Utilizador.query.filter_by(email=email).first():
            flash('Já existe um utilizador com este email.', 'danger')
            return render_template('configuracao/novo_utilizador.html',
                                    nome=nome, email=email, perfil=perfil)

        # Aviso nao-bloqueante: nome nao e chave de negocio — duas pessoas
        # podem legitimamente chamar-se igual. So avisa e sugere um email
        # diferenciado (padrao usado por Google Workspace/Microsoft 365),
        # nunca impede a criacao.
        homonimo_activo = Utilizador.query.filter(
            db.func.lower(Utilizador.nome) == nome.lower(),
            Utilizador.ativo == True
        ).first()
        if homonimo_activo:
            local, dominio = email.split('@', 1)
            sufixo = 2
            email_sugerido = f'{local}{sufixo}@{dominio}'
            while Utilizador.query.filter_by(email=email_sugerido).first():
                sufixo += 1
                email_sugerido = f'{local}{sufixo}@{dominio}'
            flash(
                f'Atenção: já existe um utilizador activo chamado "{nome}" '
                f'({homonimo_activo.email}). Se forem pessoas diferentes, considere '
                f'um email diferenciado, por exemplo "{email_sugerido}".',
                'warning'
            )

        valida, erro = validar_politica_password(password, nome, email)
        if not valida:
            flash(erro, 'danger')
            return render_template('configuracao/novo_utilizador.html',
                                    nome=nome, email=email, perfil=perfil)

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
    if u.ativo:
        # Reactivacao manual limpa o historico de tentativas falhadas —
        # senao a conta ficaria a um erro de ser bloqueada outra vez.
        u.tentativas_falhadas = 0
    db.session.commit()
    estado = 'activado' if u.ativo else 'desactivado'
    flash(f'Utilizador {u.nome} {estado} com sucesso.', 'success')
    return redirect(url_for('configuracao.utilizadores'))


@config_bp.route('/utilizadores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_utilizador(id):
    """
    Edicao de nome e perfil por um administrador — nunca da propria conta
    (segregacao de funcoes: precisa de ser outro administrador a faze-lo).
    """
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    u = Utilizador.query.get_or_404(id)
    if u.id_utilizador == current_user.id_utilizador:
        flash('Não pode editar o seu próprio nome ou perfil — peça a outro administrador.', 'danger')
        return redirect(url_for('configuracao.utilizadores'))

    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        perfil = request.form.get('perfil')

        if not nome:
            flash('O nome não pode ficar vazio.', 'danger')
            return render_template('configuracao/editar_utilizador.html', utilizador=u)
        if perfil not in ('auditor', 'administrador'):
            flash('Perfil inválido.', 'danger')
            return render_template('configuracao/editar_utilizador.html', utilizador=u)

        u.nome = nome
        u.perfil = perfil
        db.session.commit()
        flash(f'Utilizador {u.nome} actualizado com sucesso.', 'success')
        return redirect(url_for('configuracao.utilizadores'))

    return render_template('configuracao/editar_utilizador.html', utilizador=u)


@config_bp.route('/utilizadores/<int:id>/reset-password', methods=['POST'])
@login_required
def reset_password_utilizador(id):
    """
    Repoe uma password temporaria definida pelo administrador — sem fluxo
    de recuperacao por token/email, e a forma de desbloquear alguem que
    esqueceu a password. O utilizador deve troca-la em "O Meu Perfil"
    assim que conseguir entrar. Nunca aplicavel a propria conta do admin.
    """
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    u = Utilizador.query.get_or_404(id)
    if u.id_utilizador == current_user.id_utilizador:
        flash('Não pode repor a sua própria password aqui — altere-a em "O Meu Perfil".', 'danger')
        return redirect(url_for('configuracao.utilizadores'))

    password_temporaria = request.form.get('password_temporaria', '')
    valida, erro = validar_politica_password(password_temporaria, u.nome, u.email)
    if not valida:
        flash(erro, 'danger')
        return redirect(url_for('configuracao.editar_utilizador', id=u.id_utilizador))

    u.set_password(password_temporaria)
    u.tentativas_falhadas = 0
    db.session.commit()
    flash(
        f'Password de {u.nome} reposta com sucesso. Informe-o(a) da password '
        f'temporária para que a altere em "O Meu Perfil" assim que entrar.',
        'success'
    )
    return redirect(url_for('configuracao.utilizadores'))


# =============================================================================
# O MEU PERFIL (self-service — qualquer utilizador autenticado, sem admin_required)
# =============================================================================

@config_bp.route('/perfil')
@login_required
def perfil():
    """Pagina de gestao do proprio perfil. So a password e editavel aqui —
    nome e perfil sao geridos exclusivamente por outro administrador."""
    return render_template('configuracao/perfil.html')


@config_bp.route('/perfil/password', methods=['POST'])
@login_required
def alterar_password():
    """Qualquer utilizador pode mudar a sua propria password — nunca a de outro."""
    password_actual = request.form.get('password_actual', '')
    password_nova = request.form.get('password_nova', '')
    password_confirmar = request.form.get('password_confirmar', '')

    if not current_user.check_password(password_actual):
        flash('Password actual incorrecta.', 'danger')
        return redirect(url_for('configuracao.perfil'))

    if password_nova != password_confirmar:
        flash('A nova password e a confirmação não coincidem.', 'danger')
        return redirect(url_for('configuracao.perfil'))

    valida, erro = validar_politica_password(password_nova, current_user.nome, current_user.email)
    if not valida:
        flash(erro, 'danger')
        return redirect(url_for('configuracao.perfil'))

    current_user.set_password(password_nova)
    db.session.commit()
    flash('Password alterada com sucesso.', 'success')
    return redirect(url_for('configuracao.perfil'))


# =============================================================================
# IMPORTACAO DE DADOS
# =============================================================================

@config_bp.route('/importacao')
@login_required
def importacao():
    """Hub de importacao de dados."""
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    return render_template('configuracao/importacao.html')

# =============================================================================
# ROTAS DE IMPORTACAO
# =============================================================================

@config_bp.route('/importacao/colaboradores', methods=['POST'])
@login_required
def importar_colaboradores_route():
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    ficheiro = request.files.get('ficheiro')
    if not ficheiro or ficheiro.filename == '':
        flash('Nenhum ficheiro seleccionado.', 'danger')
        return redirect(url_for('configuracao.importacao'))

    sucesso, mensagem, total, erros = importar_colaboradores(ficheiro)

    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')

    if erros:
        for erro in erros[:5]:
            flash(erro, 'warning')
        if len(erros) > 5:
            flash(f'... e mais {len(erros) - 5} erro(s).', 'warning')

    return redirect(url_for('configuracao.importacao'))


@config_bp.route('/importacao/centros-custo', methods=['POST'])
@login_required
def importar_centros_route():
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    ficheiro = request.files.get('ficheiro')
    if not ficheiro or ficheiro.filename == '':
        flash('Nenhum ficheiro seleccionado.', 'danger')
        return redirect(url_for('configuracao.importacao'))

    sucesso, mensagem, total, erros = importar_centros_custo(ficheiro)

    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')

    if erros:
        for erro in erros[:5]:
            flash(erro, 'warning')
        if len(erros) > 5:
            flash(f'... e mais {len(erros) - 5} erro(s).', 'warning')

    return redirect(url_for('configuracao.importacao'))


@config_bp.route('/importacao/orcamentos', methods=['POST'])
@login_required
def importar_orcamentos_route():
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    ficheiro = request.files.get('ficheiro')
    if not ficheiro or ficheiro.filename == '':
        flash('Nenhum ficheiro seleccionado.', 'danger')
        return redirect(url_for('configuracao.importacao'))

    sucesso, mensagem, total, erros = importar_orcamentos(ficheiro)

    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')

    if erros:
        for erro in erros[:5]:
            flash(erro, 'warning')
        if len(erros) > 5:
            flash(f'... e mais {len(erros) - 5} erro(s).', 'warning')

    return redirect(url_for('configuracao.importacao'))


@config_bp.route('/importacao/aquisicoes', methods=['POST'])
@login_required
def importar_aquisicoes_route():
    if not admin_required():
        return redirect(url_for('configuracao.index'))
    ficheiro = request.files.get('ficheiro')
    if not ficheiro or ficheiro.filename == '':
        flash('Nenhum ficheiro seleccionado.', 'danger')
        return redirect(url_for('configuracao.importacao'))

    sucesso, mensagem, total, erros = importar_aquisicoes(ficheiro)

    if sucesso:
        flash(mensagem, 'success')
    else:
        flash(mensagem, 'danger')

    if erros:
        for erro in erros[:5]:
            flash(erro, 'warning')
        if len(erros) > 5:
            flash(f'... e mais {len(erros) - 5} erro(s).', 'warning')

    return redirect(url_for('configuracao.importacao'))