from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from forms.auth import LoginForm, RegisterForm
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('game.lobby'))
        flash('Invalid username or password', 'error')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html', form=form)

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            bonus_balance=10.00,  # $10 starting bonus
            balance=0.00  # Starting balance
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()

            # Auto-login after registration
            login_user(user)
            flash('Welcome! Your $10.00 bonus has been added!', 'success')
            return redirect(url_for('game.lobby'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html', form=form)

    return render_template('auth/register.html', form=form)

@auth_bp.route('/account-info')
@login_required
def account_info():
    """Return current user's account information as JSON"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'balance': float(current_user.balance),
        'bonus_balance': float(current_user.bonus_balance),
        'total_wins': current_user.total_wins,
        'total_spins': current_user.total_spins,
        'highest_win': float(current_user.highest_win),
        'rank': current_user.rank,
        'registered_on': current_user.created_at.isoformat() if current_user.created_at else None
    })

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))