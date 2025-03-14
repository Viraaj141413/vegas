from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from models import db, User, GameSession, SlotGame, LeaderboardEntry # Added LeaderboardEntry
import random

game_bp = Blueprint('game', __name__)

BET_AMOUNTS = [0.20, 0.40, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

@game_bp.route('/lobby')
@login_required
def lobby():
    games = SlotGame.query.all()
    return render_template('game/lobby.html', games=games)

@game_bp.route('/slot/<int:game_id>')
@login_required
def slot_game(game_id):
    game = SlotGame.query.get_or_404(game_id)
    return render_template('game/slot.html', 
                         game=game, 
                         bet_amounts=BET_AMOUNTS,
                         user=current_user)

@game_bp.route('/api/spin', methods=['POST'])
@login_required
def spin():
    data = request.get_json()
    bet_amount = float(data.get('bet_amount', 0.20))
    game_id = int(data.get('game_id'))
    use_bonus = data.get('use_bonus', False)

    if bet_amount not in BET_AMOUNTS:
        return jsonify({'error': 'Invalid bet amount'}), 400

    game = SlotGame.query.get_or_404(game_id)

    # Check if user has sufficient balance
    if use_bonus:
        if current_user.bonus_balance < bet_amount:
            return jsonify({'error': 'Insufficient bonus balance'}), 400
    else:
        if current_user.balance < bet_amount:
            return jsonify({'error': 'Insufficient balance'}), 400

    # Generate spin result
    result = generate_spin_result(game)
    win_amount = calculate_win_amount(result, bet_amount, game)

    # Update user balance
    if use_bonus:
        current_user.bonus_balance -= bet_amount
        if win_amount > 0:
            current_user.bonus_balance += win_amount
    else:
        current_user.balance -= bet_amount
        if win_amount > 0:
            current_user.balance += win_amount

    # Record game session
    session = GameSession(
        user_id=current_user.id,
        game_type=game.name,
        bet_amount=bet_amount,
        win_amount=win_amount,
        used_bonus=use_bonus,
        is_jackpot=result.get('jackpot', False),
        wild_multiplier=result.get('wild_multiplier', 1)
    )

    # Update user statistics
    current_user.total_spins += 1
    if win_amount > 0:
        current_user.total_wins += 1
        if win_amount > current_user.highest_win:
            current_user.highest_win = win_amount

    db.session.add(session)
    db.session.commit()

    return jsonify({
        'result': result,
        'win_amount': win_amount,
        'new_balance': current_user.bonus_balance if use_bonus else current_user.balance,
        'bonus_balance': current_user.bonus_balance,
        'regular_balance': current_user.balance
    })

@game_bp.route('/api/toggle-auto-spin', methods=['POST'])
@login_required
def toggle_auto_spin():
    current_user.auto_spin_active = not current_user.auto_spin_active
    db.session.commit()
    return jsonify({'auto_spin_active': current_user.auto_spin_active})

@game_bp.route('/api/set-bet', methods=['POST'])
@login_required
def set_bet():
    data = request.get_json()
    bet_amount = float(data.get('bet_amount', 0.20))

    if bet_amount not in BET_AMOUNTS:
        return jsonify({'error': 'Invalid bet amount'}), 400

    current_user.current_bet = bet_amount
    db.session.commit()
    return jsonify({'current_bet': current_user.current_bet})

def generate_spin_result(game):
    symbols = ['🍒', '💎', '7️⃣', '🎰', '⭐', '🎲', '🎮', '🎯']
    result_symbols = []
    wild_multiplier = 1
    is_jackpot = False

    # Generate random symbols for each reel
    for _ in range(3):  # 3 reels
        symbol = random.choice(symbols)
        result_symbols.append(symbols.index(symbol))

    # Check for special combinations
    if all(s == result_symbols[0] for s in result_symbols):
        if result_symbols[0] == symbols.index('7️⃣'):
            is_jackpot = True
        elif result_symbols[0] == symbols.index('💎'):
            wild_multiplier = 2

    return {
        'symbols': result_symbols,
        'wild_multiplier': wild_multiplier,
        'jackpot': is_jackpot,
        'paylines': []  # Will be used for future payline implementations
    }

def calculate_win_amount(result, bet_amount, game):
    base_multipliers = [3, 50, 100, 15, 20, 10, 8, 5]  # Corresponds to symbol order

    if result['jackpot']:
        return bet_amount * 100  # Jackpot multiplier

    symbols = result['symbols']
    if len(set(symbols)) == 1:  # All symbols match
        base_win = bet_amount * base_multipliers[symbols[0]]
        return base_win * result['wild_multiplier']

    return 0.0  # No win


@game_bp.route('/api/claim-prize/<int:match_id>', methods=['POST'])
@login_required
def claim_prize(match_id):
    match = LeaderboardEntry.query.get_or_404(match_id)

    if match.user_id != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403

    if match.claimed:
        return jsonify({'error': 'Prize already claimed'}), 400

    # Add prize money to user's balance
    current_user.balance += match.prize_awarded
    match.claimed = True

    db.session.commit()

    return jsonify({
        'success': True,
        'prize_amount': match.prize_awarded,
        'new_balance': current_user.balance
    })

@game_bp.route('/match-history')
@login_required
def match_history():
    active_matches = LeaderboardEntry.query.filter_by(
        user_id=current_user.id,
        round_complete=False
    ).order_by(LeaderboardEntry.timestamp.desc()).all()

    completed_matches = LeaderboardEntry.query.filter_by(
        user_id=current_user.id,
        round_complete=True
    ).order_by(LeaderboardEntry.timestamp.desc()).limit(10).all()

    return render_template('game/match_history.html',
                         active_matches=active_matches,
                         completed_matches=completed_matches)