from urllib.parse import urlparse
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.utilizador import Utilizador
from app import limiter, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

MAX_TENTATIVAS_FALHADAS = 3


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    """Pagina de login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        utilizador = Utilizador.query.filter_by(email=email).first()

        # Conta activa e password correcta — sucesso.
        if utilizador and utilizador.ativo and utilizador.check_password(password):
            utilizador.tentativas_falhadas = 0
            db.session.commit()

            login_user(utilizador)
            flash(f'Bem-vindo, {utilizador.nome}.', 'success')

            # Redireciona para a pagina que o utilizador tentou aceder.
            # So aceita caminhos relativos — um 'next' absoluto permitiria
            # redireccionar para um dominio externo apos o login (open redirect).
            proxima = request.args.get('next')
            destino_seguro = (
                proxima
                and urlparse(proxima).netloc == ''
                and urlparse(proxima).scheme == ''
            )
            return redirect(proxima if destino_seguro else url_for('main.index'))

        # Password errada numa conta ainda activa — conta a tentativa e,
        # ao atingir o limite, desactiva a conta (mesmo campo 'ativo' usado
        # pelo administrador — fica bloqueada ate ser reactivada manualmente).
        if utilizador and utilizador.ativo:
            utilizador.tentativas_falhadas += 1
            if utilizador.tentativas_falhadas >= MAX_TENTATIVAS_FALHADAS:
                utilizador.ativo = False
                db.session.commit()
                flash(
                    'Conta bloqueada apos 3 tentativas falhadas. '
                    'Contacte um administrador para a reactivar.',
                    'danger'
                )
                return render_template('auth/login.html')
            db.session.commit()

        # Mensagem generica em todos os outros casos (email inexistente,
        # conta ja inactiva, password errada abaixo do limite) — nao revela
        # qual destes cenarios ocorreu, para nao facilitar enumeracao de contas.
        flash('Email ou password incorrectos.', 'danger')
        return render_template('auth/login.html')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Termina a sessao."""
    logout_user()
    flash('Sessão terminada com sucesso.', 'info')
    return redirect(url_for('auth.login'))