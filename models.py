from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    balance = db.Column(db.Float, default=0.0)
    bonus_balance = db.Column(db.Float, default=10.0)  # Changed to $10 bonus
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Game statistics
    total_wins = db.Column(db.Integer, default=0)
    total_spins = db.Column(db.Integer, default=0)
    highest_win = db.Column(db.Float, default=0.0)
    rank = db.Column(db.String(20), default='Bronze')
    first_deposit_bonus_used = db.Column(db.Boolean, default=False)
    auto_spin_active = db.Column(db.Boolean, default=False)
    current_bet = db.Column(db.Float, default=0.20)

    # Daily bonus tracking
    last_daily_bonus = db.Column(db.DateTime)
    daily_bonus_streak = db.Column(db.Integer, default=0)
    last_wheel_spin = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def can_withdraw(self):
        return self.balance >= 20.0  # Minimum withdrawal amount

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # 'slots', 'bingo', 'bubble', 'solitaire'
    bet_amount = db.Column(db.Float, nullable=False)
    win_amount = db.Column(db.Float, nullable=False)
    used_bonus = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    points_earned = db.Column(db.Integer, default=0)  # For solitaire and casual games
    is_jackpot = db.Column(db.Boolean, default=False)
    wild_multiplier = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref=db.backref('game_sessions', lazy=True))

class SlotGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    theme = db.Column(db.String(50))  # e.g., 'mahjong', 'diamond', 'japanese'
    reels = db.Column(db.Integer, default=5)
    paylines = db.Column(db.Integer)
    min_bet = db.Column(db.Float, default=0.20)
    max_bet = db.Column(db.Float, default=10.0)
    jackpot_amount = db.Column(db.Float, default=1000.0)
    rtp = db.Column(db.Float)  # Return to Player percentage

class CashGame(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 'Bubble Cash', 'Solitaire Stars'
    game_type = db.Column(db.String(50))  # 'bubble', 'solitaire', 'bingo'
    min_entry = db.Column(db.Float, default=0.50)
    max_entry = db.Column(db.Float, default=20.0)
    current_jackpot = db.Column(db.Float, default=100.0)
    active = db.Column(db.Boolean, default=True)
    points_to_cash_ratio = db.Column(db.Float, default=100.0)  # Points needed for $1

class DailyBonus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer, nullable=False)  # Day in streak (1-7)
    bonus_amount = db.Column(db.Float, nullable=False)
    requires_streak = db.Column(db.Boolean, default=True)

class WheelPrize(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prize_type = db.Column(db.String(50))  # 'cash', 'bonus', 'free_spins'
    amount = db.Column(db.Float)
    probability = db.Column(db.Float)  # Probability of landing on this prize
    active = db.Column(db.Boolean, default=True)

class PaymentLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    paypal_link = db.Column(db.String(255), nullable=False)
    bonus_amount = db.Column(db.Float, default=0.0)  # The bonus amount given
    description = db.Column(db.String(100))  # e.g., "BEST DEAL! Recharge $12 get $18!"
    is_featured = db.Column(db.Boolean, default=False)  # Highlight special deals

    @property
    def total_value(self):
        return self.amount + self.bonus_amount

    @property
    def bonus_percentage(self):
        return (self.bonus_amount / self.amount) * 100 if self.amount > 0 else 0

class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Could be points or money won
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    round_id = db.Column(db.String(36), nullable=False)  # To group entries by game round
    rank = db.Column(db.Integer)  # Position on leaderboard
    prize_awarded = db.Column(db.Float, default=0.0)

    user = db.relationship('User', backref=db.backref('leaderboard_entries', lazy=True))