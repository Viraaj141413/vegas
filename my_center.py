from flask import Blueprint, render_template, jsonify, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from models import db, User, DailyBonus, WheelPrize, CashGame
import random

my_center_bp = Blueprint('my_center', __name__)

@my_center_bp.route('/my-center')
@login_required
def my_center():
    # Get active cash games
    cash_games = CashGame.query.filter_by(active=True).all()

    # Check if user can claim daily bonus and spin wheel
    can_claim_daily_bonus_flag = can_claim_daily_bonus()
    can_spin_wheel_flag = can_spin_wheel()

    return render_template('my_center/dashboard.html',
                         user=current_user,
                         cash_games=cash_games,
                         can_claim_daily=can_claim_daily_bonus_flag,
                         can_spin_wheel=can_spin_wheel_flag)

@my_center_bp.route('/claim-daily-bonus')
@login_required
def claim_daily_bonus():
    if not can_claim_daily_bonus():
        return jsonify({'error': 'Daily bonus already claimed'}), 400

    streak_day = current_user.daily_bonus_streak + 1
    if streak_day > 7:
        streak_day = 1

    bonus = DailyBonus.query.filter_by(day=streak_day).first()
    current_user.bonus_balance += bonus.bonus_amount
    current_user.daily_bonus_streak = streak_day
    current_user.last_daily_bonus = datetime.utcnow()

    db.session.commit()
    return jsonify({
        'success': True,
        'bonus_amount': bonus.bonus_amount,
        'streak_day': streak_day,
        'new_bonus_balance': current_user.bonus_balance
    })

@my_center_bp.route('/spin-wheel')
@login_required
def spin_wheel():
    if not can_spin_wheel():
        return jsonify({'error': 'Wheel already spun today'}), 400

    prizes = WheelPrize.query.filter_by(active=True).all()
    total_probability = sum(prize.probability for prize in prizes)
    random_value = random.random() * total_probability

    current_sum = 0
    won_prize = None
    for prize in prizes:
        current_sum += prize.probability
        if random_value <= current_sum:
            won_prize = prize
            break

    if won_prize.prize_type == 'cash':
        current_user.balance += won_prize.amount
    elif won_prize.prize_type == 'bonus':
        current_user.bonus_balance += won_prize.amount

    current_user.last_wheel_spin = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'prize_type': won_prize.prize_type,
        'amount': won_prize.amount
    })

@my_center_bp.route('/more-games')
@login_required
def more_games():
    active_games = CashGame.query.filter_by(active=True).all()
    return render_template('my_center/more_games.html', games=active_games)

def can_claim_daily_bonus():
    if not current_user.last_daily_bonus:
        return True
    next_bonus_time = current_user.last_daily_bonus + timedelta(days=1)
    return datetime.utcnow() >= next_bonus_time

def can_spin_wheel():
    if not current_user.last_wheel_spin:
        return True
    next_spin_time = current_user.last_wheel_spin + timedelta(days=1)
    return datetime.utcnow() >= next_spin_time