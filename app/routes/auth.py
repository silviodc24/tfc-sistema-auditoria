from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.utilizador import Utilizador

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina de login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        utilizador = Utilizador.query.filter_by(email=email, ativo=True).first()

        if not utilizador or not utilizador.check_password(password):
            flash('Email ou password incorrectos.', 'danger')
            return render_template('auth/login.html')

        login_user(utilizador)
        flash(f'Bem-vindo, {utilizador.nome}.', 'success')

        # Redireciona para a pagina que o utilizador tentou aceder
        proxima = request.args.get('next')
        return redirect(proxima or url_for('main.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Termina a sessao."""
    logout_user()
    flash('Sessão terminada com sucesso.', 'info')
    return redirect(url_for('auth.login'))